import redis.asyncio as redis
from redis.asyncio.sentinel import Sentinel
from functools import lru_cache
from typing import AsyncGenerator, List, Tuple

from src.config import (
    DB_HOST,
    DB_PORT,
    REDIS_DB,
    USE_REDIS_SENTINEL,
    REDIS_SENTINELS,
    REDIS_MASTER_NAME,
    logger,
)

# ---------- helpers ----------

def _parse_sentinels(value: str) -> List[Tuple[str, int]]:
    """
    "host1:26379,host2:26379" -> [(host1,26379),(host2,26379)]
    """
    result = []
    for item in value.split(","):
        host, port = item.strip().split(":")
        result.append((host, int(port)))
    return result


@lru_cache(maxsize=1)
def _get_sentinel() -> Sentinel:
    sentinels = _parse_sentinels(REDIS_SENTINELS)
    logger.info(f"Connecting to Redis Sentinel(s): {sentinels}")
    return Sentinel(
        sentinels,
        socket_timeout=0.5,
        decode_responses=True,
        db=REDIS_DB,
    )


# ---------- FastAPI dependency ----------

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Redis dependency with Sentinel support.
    """

    if USE_REDIS_SENTINEL:
        sentinel = _get_sentinel()
        client = sentinel.master_for(
            service_name=REDIS_MASTER_NAME,
            socket_timeout=0.5,
        )
        logger.debug("Using Redis via Sentinel")

    else:
        client = redis.Redis(
            host=DB_HOST,
            port=DB_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_timeout=0.5,
        )
        logger.debug("Using direct Redis connection")

    try:
        # sanity check
        await client.ping()
        yield client
    finally:
        await client.aclose()
