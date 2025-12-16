import asyncio
import json
import redis.asyncio as aioredis

from src.config import logger, DB_HOST, DB_PORT, DEVICE_COMMAND_CHANNEL
from src.services.commands_service import process_command_message

async def pubsub_listener():
    """
    Sets up the Redis Pub/Sub connection and listens forever.
    This runs as a background task.
    """
    redis = aioredis.Redis(host=DB_HOST, port=DB_PORT)
    await redis.ping()
    pubsub = redis.pubsub()

    try:
        await pubsub.subscribe(DEVICE_COMMAND_CHANNEL)
        logger.info(f"Subscribed to Redis channel: {DEVICE_COMMAND_CHANNEL}")

        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = message['data']
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')

                    command_payload = json.loads(data)
                    asyncio.create_task(process_command_message(redis, command_payload))

                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON message: {message['data']}")
                except Exception as e:
                    logger.error(f"Error in Pub/Sub message stream: {e}")

    except ConnectionRefusedError:
        logger.critical("Could not connect to Redis for Pub/Sub. Listener failed to start.")
    finally:
        await pubsub.unsubscribe(DEVICE_COMMAND_CHANNEL)
        await redis.aclose()
        logger.info("Pub/Sub listener connection closed.")
