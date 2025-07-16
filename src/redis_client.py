import aioredis
from src.config import settings


_redis = None

def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_CACHE_URL
        )
    return _redis

    
    

async def set_to_redis(key, value, ex=None):
    
    redis = get_redis()
    
    return await redis.set(f"{settings.REDIS_NAMESPACE}:{key}", value, ex=ex)


async def get_from_redis(key):
    redis = get_redis()
    return await redis.get(f"{settings.REDIS_NAMESPACE}:{key}")