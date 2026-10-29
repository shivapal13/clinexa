from app.core.redis import redis_client
import json
import logging
from datetime import date
from typing import Any
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


def get_json(key: str):
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except (RedisError, json.JSONDecodeError):
        logger.warning("Redis cache read failed for key %s", key, exc_info=True)
    return None


def set_json(key: str, value: Any, ttl: int = 300):
    try:
        redis_client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl,
        )
    except RedisError:
        logger.warning("Redis cache write failed for key %s", key, exc_info=True)


def delete_key(key: str):
    try:
        redis_client.delete(key)
    except RedisError:
        logger.warning("Redis cache invalidation failed for key %s", key, exc_info=True)


# FIX: the old codebase called delete_key("pattern:*") which deleted a
# literal key named "pattern:*". Pattern-based invalidation requires SCAN.
def delete_pattern(pattern: str):
    """Delete all keys matching a Redis glob pattern (e.g. 'availability:doctor:5:*')."""
    cursor = 0
    try:
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break
    except RedisError:
        logger.warning(
            "Redis pattern cache invalidation failed for %s", pattern, exc_info=True
        )


def invalidate_custom_availability(doctor_id: int, target_date: date):
    delete_key(f"custom:doctor:{doctor_id}")
    delete_key(f"custom:doctor:{doctor_id}:{target_date}")
    delete_key(f"availability:doctor:{doctor_id}:{target_date}")
