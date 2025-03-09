import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class ProcessingTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to measure and add processing time to response headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request and add processing time to response headers.

        Args:
            request (Request): The incoming request.
            call_next (RequestResponseEndpoint): The next request handler in
            the middleware chain.

        Returns:
            Response: The response with added X-Process-Time header.
        """
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
