from redis.asyncio import Redis
import ssl
from src.config import settings


def get_redis():

    
    return Redis.from_url(
        settings.REDIS_CACHE_URL
    )

async def set_to_redis(key, value, ex=None):
    
    redis = get_redis()
    
    return await redis.set(f"{settings.REDIS_NAMESPACE}:{key}", value, ex=ex)


async def get_from_redis(key):
    redis = get_redis()
    return await redis.get(f"{settings.REDIS_NAMESPACE}:{key}")