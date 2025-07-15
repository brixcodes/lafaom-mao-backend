from redis.asyncio import Redis
import ssl
from src.config import settings

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE



def get_redis():
    return Redis.from_url(settings.REDIS_CACHE_URL,ssl=ssl_context)

async def set_to_redis(key, value):
    
    redis = get_redis()
    return await redis.set(f"{settings.REDIS_NAMESPACE}:{key}", value)


async def get_from_redis(key):
    redis = get_redis()
    return await redis.get(f"{settings.REDIS_NAMESPACE}:{key}")