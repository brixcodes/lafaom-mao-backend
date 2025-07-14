import aioredis
from src.config import settings



redis = aioredis.from_url(settings.REDIS_CACHE_URL,decode_responses=True)
