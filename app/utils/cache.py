import redis.asyncio as aioredis
import json
from app.core.config import settings
from typing import Any, Optional

redis_client: Optional[aioredis.Redis] = None

async def init_redis_cache():
    global redis_client
    redis_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
    print("Redis cache initialized.")

async def get_cached_data(key: str) -> Any  :
    if not redis_client:
        await init_redis_cache()
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cached_data(key: str, data: Any, ttl: int = 300):
    if not redis_client:
        await init_redis_cache()
    await redis_client.setex(key, ttl, json.dumps(data))

async def invalidate_cache(key: str):
    if not redis_client:
        await init_redis_cache()
    await redis_client.delete(key)