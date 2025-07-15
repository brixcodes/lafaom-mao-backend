from redis.asyncio import Redis
import ssl
from src.config import settings


def get_redis():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED 
    
    return Redis.from_url(
        settings.REDIS_CACHE_URL,
        ssl=True
    )

async def set_to_redis(key, value, ex=None):
    
    redis = get_redis()
    
    return await redis.set(f"{settings.REDIS_NAMESPACE}:{key}", value, ex=ex)


async def get_from_redis(key):
    redis = get_redis()
    return await redis.get(f"{settings.REDIS_NAMESPACE}:{key}")