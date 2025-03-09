from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class TestClientIPOverrideMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, client_host: str, client_port: int = 12345):
        super().__init__(app)
        self.client_host = client_host
        self.client_port = client_port

    async def dispatch(self, request, call_next):
        """Override the client IP address in the ASGI scope."""

        request.scope["client"] = (self.client_host, self.client_port)
        return await call_next(request)
