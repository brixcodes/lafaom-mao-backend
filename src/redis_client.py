import aioredis
import ssl
from src.config import settings

ssl_context = ssl.create_default_context()
# Pour ignorer les certificats non signés (non recommandé pour prod)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
redis = aioredis.from_url(settings.REDIS_CACHE_URL, ssl=ssl_context,decode_responses=True)
