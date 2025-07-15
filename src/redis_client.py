import ssl
from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.connection import SSLConnection
from src.config import settings


_redis = None

def get_redis():
    global _redis
    if _redis is None:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # ⚠️ pour dev uniquement

        _redis = Redis(
            connection_pool=ConnectionPool.from_url(
                url=settings.REDIS_CACHE_URL,
                connection_class=SSLConnection,
                ssl_context=ssl_context,
            )
        )
    return _redis

    
    

async def set_to_redis(key, value, ex=None):
    
    redis = get_redis()
    
    return await redis.set(f"{settings.REDIS_NAMESPACE}:{key}", value, ex=ex)


async def get_from_redis(key):
    redis = get_redis()
    return await redis.get(f"{settings.REDIS_NAMESPACE}:{key}")