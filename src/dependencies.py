import redis.asyncio as redis
from src.config import DB_HOST, DB_PORT, REDIS_DB

async def get_redis():
    client = redis.Redis(
        host=DB_HOST,
        port=DB_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.close()
