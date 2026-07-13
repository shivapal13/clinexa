from app.core.redis import redis_client
import json


def get_json(key:str):
    data=redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_json(key:str,value:dict,ttl:int=300):
    redis_client.set(
        key,
        json.dumps(value),
        ex=ttl
    )

def delete_key(key:str):
    redis_client.delete(key)  


def delete_pattern(pattern: str):
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)