from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """
    Extract real client IP when running behind proxies (Render, AWS, Nginx).
    Falls back to direct socket remote address.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Configure SlowAPI with in-memory fallback and swallow_errors=True
# so that if Redis is offline or unreachable, user requests (e.g. login/register)
# never crash with 500 Internal Server Error.
limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=settings.REDIS_URL if settings.REDIS_URL else "memory://",
    strategy="fixed-window",
    in_memory_fallback_enabled=True,
    swallow_errors=True,
)
