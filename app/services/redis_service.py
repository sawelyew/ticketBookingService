from redis.asyncio import Redis


class RedisService:
    def __init__(self, redis: Redis):
        self.redis = redis


    async def get_locked_seats(self, event_id: int) -> set[int]:
        pattern = f"lock:event:{event_id}:seat:*"
        locked_seat_ids = set()

        async for key in self.redis.scan_iter(match=pattern):
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            seat_id = int(key_str.split(":")[-1])
            locked_seat_ids.add(seat_id)

        return locked_seat_ids