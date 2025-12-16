import asyncio
import json
import os
from pathlib import Path
import redis.asyncio as aioredis
from src.config import DB_HOST, DB_PORT, REDIS_DB


DATA_PATH = Path(__file__).resolve().parents[1] / "tests" / "test_devices.json"
NO_CLEAN = os.getenv("SEED_NO_CLEAN", "false").lower() in ("true", "1", "t")


async def clear_devices(r):
    """Deletes all device and device history keys."""
    deleted = 0

    async for key in r.scan_iter(match="device:*"):
        await r.delete(key)
        deleted += 1

    async for key in r.scan_iter(match="device:history:*"):
        await r.delete(key)
        deleted += 1

    print(f"🧹 Cleared {deleted} Redis keys")


async def seed_database():
    r = aioredis.Redis(
        host=DB_HOST,
        port=DB_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )

    try:
        await r.ping()
        print(f"Connected to Redis at {DB_HOST}:{DB_PORT}, db={REDIS_DB}")
        print(f"Loading devices from: {DATA_PATH}")

        if not NO_CLEAN:
            await clear_devices(r)
        else:
            print("SEED_NO_CLEAN=true , skipping Redis cleanup")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            devices = json.load(f)

        saved_count = 0

        for device in devices:
            device_id = device.get("id")
            if not device_id:
                continue

            key = f"device:{device_id}"
            data = {
                k: str(v).lower() if isinstance(v, bool) else str(v)
                for k, v in device.items()
                if k != "id"
            }

            await r.hset(key, mapping=data)
            print(f"Seeded {key}")
            saved_count += 1

        print("-" * 40)
        print(f"Successfully seeded {saved_count} devices")

    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(seed_database())
