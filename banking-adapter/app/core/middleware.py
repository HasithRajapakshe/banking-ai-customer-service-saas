import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Reads X-Correlation-ID from incoming request headers.
    If missing or empty, generates a new UUID.
    Stores it in request.state.correlation_id and adds
    it to the outgoing response headers.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:

        correlation_id = (
            request.headers.get("X-Correlation-ID", "").strip()
            or str(uuid.uuid4())
        )

        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
        except Exception:
            raise
        else:
            response.headers["X-Correlation-ID"] = correlation_id
            return response
