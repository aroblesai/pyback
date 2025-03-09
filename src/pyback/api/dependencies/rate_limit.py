from collections.abc import Callable

from fastapi import Request

from pyback.config.rate_limit import RateLimitConfig


def rate_limit(
    scope: RateLimitConfig.Scope,
    times: int | None = None,
    seconds: int | None = None,
    prefix: str | None = None,
    key_func: Callable[[Request], str] | None = None,
):
    """Create a rate limiter dependency with the specified configuration.

    Args:
        scope: The rate limit scope (PUBLIC, AUTHENTICATED, ADMIN)
        times: Optional override for number of requests
        seconds: Optional override for time window
        prefix: Optional override for Redis key prefix
        key_func: Optional custom key generation function

    Returns:
        A dependency that can be used at the router or endpoint level
    """
    return RateLimitConfig.get_rate_limiter(
        scope=scope,
        times=times,
        seconds=seconds,
        prefix=prefix,
        key_func=key_func,
    )
