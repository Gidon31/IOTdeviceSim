import asyncio
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from src.config import DB_HOST, DB_PORT, REDIS_DB, logger

_client: redis.Redis | None = None
_lock = asyncio.Lock()


def build_client() -> redis.Redis:
    return redis.Redis(
        host=DB_HOST,
        port=DB_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


async def get_redis_client() -> redis.Redis:
    global _client

    if _client is not None:
        try:
            await _client.ping()
            return _client
        except (ConnectionError, TimeoutError):
            logger.warning("Redis connection lost. Reconnecting...")
            _client = None

    async with _lock:
        if _client is None:
            _client = build_client()
            await _client.ping()
        return _client


async def close_redis_client() -> None:
    global _client
    async with _lock:
        if _client is not None:
            await _client.aclose()
            _client = None
