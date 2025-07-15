from redis.asyncio import Redis
import ssl
from src.config import settings

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE




redis = Redis.from_url(settings.REDIS_CACHE_URL,ssl=ssl_context)
