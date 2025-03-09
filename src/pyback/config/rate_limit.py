from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address, ip_network
import time
from typing import Any

from fastapi import Request
from fastapi_limiter.depends import RateLimiter
from loguru import logger

from pyback.core.exceptions import BadRequestError


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""

    times: int
    seconds: int
    prefix: str


class RateLimitConfig:
    """Enhanced rate limiting configuration with security features."""

    class Scope(Enum):
        """Predefined rate limit scopes with clear documentation."""

        PUBLIC = "public"  # Unauthenticated public access
        AUTHENTICATED = "authenticated"  # Regular authenticated users
        ADMIN = "admin"  # Administrative access
        API = "api"  # API key based access

    # Security configuration
    MAX_HEADER_LENGTH = 1024  # Maximum length for header values
    VALIDATION_TIMEOUT = 1.0  # Seconds for IP validation timeout
    MAX_FORWARDED_IPS = 10  # Maximum number of IPs in X-Forwarded-For

    # Trusted proxy networks (private network ranges)
    TRUSTED_PROXIES = frozenset(
        [
            ip_network("10.0.0.0/8"),  # RFC1918 private network
            ip_network("172.16.0.0/12"),  # RFC1918 private network
            ip_network("192.168.0.0/16"),  # RFC1918 private network
            ip_network("127.0.0.0/8"),  # Localhost
        ],
    )

    # Rate limit configurations for different scopes
    DEFAULT_LIMITS: dict[Scope, RateLimitRule] = {
        Scope.PUBLIC: RateLimitRule(times=10, seconds=60, prefix="public"),
        Scope.AUTHENTICATED: RateLimitRule(times=100, seconds=60, prefix="auth"),
        Scope.ADMIN: RateLimitRule(times=1000, seconds=60, prefix="admin"),
        Scope.API: RateLimitRule(times=200, seconds=60, prefix="api"),
    }

    @classmethod
    @contextmanager
    def timeout(cls, seconds: float):
        """Context manager for timeout operations."""
        deadline = time.time() + seconds
        yield
        if time.time() > deadline:
            raise TimeoutError

    @classmethod
    def sanitize_header_value(cls, value: str | None) -> str:
        """Sanitize and truncate header values."""
        if not value:
            return ""
        return str(value)[: cls.MAX_HEADER_LENGTH].strip()

    @classmethod
    def is_trusted_proxy(cls, ip: str) -> bool:
        """Check if an IP belongs to trusted proxy networks with timeout protection."""
        try:
            with cls.timeout(cls.VALIDATION_TIMEOUT):
                addr = ip_address(ip)
                return any(addr in network for network in cls.TRUSTED_PROXIES)
        except (ValueError, TimeoutError) as e:
            logger.warning(f"IP validation failed for {ip}: {str(e)}")
            return False

    @classmethod
    def get_real_client_ip(cls, request: Request) -> str:
        """Get the real client IP with enhanced security and validation."""
        immediate_client_ip = request.client.host

        # Always validate immediate client IP
        if not cls.is_valid_ip(immediate_client_ip):
            logger.warning(f"Invalid immediate client IP: {immediate_client_ip}")
            raise BadRequestError("Invalid client IP")

        forwarded_for = cls.sanitize_header_value(
            request.headers.get("x-forwarded-for"),
        )

        if forwarded_for:
            ips = [ip.strip() for ip in forwarded_for.split(",")][
                : cls.MAX_FORWARDED_IPS
            ]

            # Validate the entire proxy chain
            if len(ips) > 1:
                # Check if the connecting IP is a trusted proxy
                if not cls.is_trusted_proxy(immediate_client_ip):
                    logger.warning(
                        f"Untrusted proxy attempt from {immediate_client_ip}",
                    )
                    return immediate_client_ip

                # Verify the chain of trust
                # (all but the first IP should be trusted proxies)
                for proxy_ip in ips[1:]:
                    if not cls.is_trusted_proxy(proxy_ip):
                        logger.warning(f"Broken proxy chain at IP: {proxy_ip}")
                        return immediate_client_ip

                # Use the first IP if it's valid
                if cls.is_valid_ip(ips[0]):
                    return ips[0]

            elif len(ips) == 1:
                # If there's exactly one IP in X-Forwarded-For, use it if it's valid.
                if cls.is_valid_ip(ips[0]):
                    return ips[0]

        # Fallback to X-Real-IP with validation
        real_ip = cls.sanitize_header_value(request.headers.get("x-real-ip"))
        if real_ip and cls.is_valid_ip(real_ip):
            return real_ip

        return immediate_client_ip

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address format."""
        try:
            ip_address(ip)
            return True
        except ValueError:
            return False

    @classmethod
    def get_user_identifier(cls, request: Request) -> str | None:
        """Get user identifier with type validation."""
        if hasattr(request.state, "user"):
            user = getattr(request.state.user, "id", None)
            return str(user) if user is not None else None
        return None

    @classmethod
    def get_api_key(cls, request: Request) -> str | None:
        """Get and validate API key from headers."""
        api_key = cls.sanitize_header_value(request.headers.get("x-api-key"))
        return api_key if api_key else None

    @classmethod
    async def generate_key(cls, request: Request, prefix: str) -> str:
        """Generate a comprehensive rate limit key with multiple identifiers."""
        components = [prefix]

        # Add all available identifiers
        identifiers = {
            "user": cls.get_user_identifier(request),
            "api": cls.get_api_key(request),
            "ip": cls.get_real_client_ip(request),
            "path": request.url.path,
            "method": request.method,
        }

        # Add non-None identifiers to the key
        components.extend(
            f"{key}:{value}" for key, value in identifiers.items() if value is not None
        )

        return ":".join(components)

    @classmethod
    def get_rate_limiter(
        cls,
        scope: Scope,
        times: int | None = None,
        seconds: int | None = None,
        prefix: str | None = None,
        key_func: Callable[[Request], Any] | None = None,
    ) -> RateLimiter:
        """Get a configured rate limiter with validation."""
        try:
            config = cls.DEFAULT_LIMITS[scope]
        except KeyError:
            logger.error(f"Invalid rate limit scope: {scope}")
            raise ValueError(f"Invalid rate limit scope: {scope}")

        # Override default configuration if provided
        rule = RateLimitRule(
            times=times or config.times,
            seconds=seconds or config.seconds,
            prefix=prefix or config.prefix,
        )

        async def async_key_generator(req: Request) -> str:
            return await cls.generate_key(req, rule.prefix)

        return RateLimiter(
            times=rule.times,
            seconds=rule.seconds,
            identifier=key_func or async_key_generator,
        )
