from redis.asyncio import Redis
import json
import hashlib

from app.core.config import settings

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis() -> Redis:
    return redis_client


def _generate_event_cache_key(date_from, date_to, venue_name, search, page, page_size):
    params = {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "venue_name": venue_name,
        "search": search,
        "page": page,
        "page_size": page_size,
    }
    params_str = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()
    return f"events:list:{params_hash}"