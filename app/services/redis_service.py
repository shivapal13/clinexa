from app.core.redis import redis_client
import json
import logging
from datetime import date
from typing import Any
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


def get_json(key: str):
    if redis_client is None:
        return None
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except (RedisError, json.JSONDecodeError) as exc:
        logger.debug("Redis cache read skipped for key %s: %s", key, exc)
    return None


def set_json(key: str, value: Any, ttl: int = 300):
    if redis_client is None:
        return
    try:
        redis_client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl,
        )
    except RedisError as exc:
        logger.debug("Redis cache write skipped for key %s: %s", key, exc)


def delete_key(key: str):
    if redis_client is None:
        return
    try:
        redis_client.delete(key)
    except RedisError as exc:
        logger.debug("Redis cache invalidation skipped for key %s: %s", key, exc)


def delete_pattern(pattern: str):
    """Delete all keys matching a Redis glob pattern (e.g. 'availability:doctor:5:*')."""
    if redis_client is None:
        return
    cursor = 0
    try:
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break
    except RedisError as exc:
        logger.debug("Redis pattern cache invalidation skipped for %s: %s", pattern, exc)


def invalidate_custom_availability(doctor_id: int, target_date: date):
    delete_key(f"custom:doctor:{doctor_id}")
    delete_key(f"custom:doctor:{doctor_id}:{target_date}")
    delete_key(f"availability:doctor:{doctor_id}:{target_date}")
