from redis import Redis
from app.core.config import settings

redis_client = None

if (
    settings.REDIS_URL
    and settings.REDIS_URL.strip()
    and not settings.REDIS_URL.startswith("memory://")
):
    try:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
    except Exception:
        redis_client = None
