import asyncio
from contextlib import asynccontextmanager
import os

import uvicorn
from fastapi import FastAPI

from src.config import APP_HOST, APP_PORT, APP_RELOAD, APP_LOG_LEVEL
from src.routers.device import router as device_router
from src.infrastructure.pubsub_listener import pubsub_listener

from fastapi_mcp import FastApiMCP


listener_task = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global listener_task

    if os.getenv("ENABLE_PUBSUB", "true").lower() == "true":
        listener_task = asyncio.create_task(pubsub_listener())

    yield

    if listener_task and not listener_task.done():
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="IOT device simulator", lifespan=lifespan)
app.include_router(device_router)

mcp = FastApiMCP(app)

mcp.mount_http()


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_RELOAD,
        log_level=APP_LOG_LEVEL,
    )
