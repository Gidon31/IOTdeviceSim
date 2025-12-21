import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DOTENV_PATH = PROJECT_DIR / ".env"

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()

level = getattr(logging, APP_LOG_LEVEL, None)
if not isinstance(level, int):
    level = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(level=level)
logger = logging.getLogger("iot-sim-logger")

if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH, override=True)
else:
    logger.warning(f".env file not found at {DOTENV_PATH}")

DB_HOST = os.getenv("DB_HOST") or os.getenv("REDIS_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT") or os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

API_KEY = os.getenv("API_KEY")
APP_MODULE = os.getenv("APP_MODULE", "src.app:app")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_RELOAD = os.getenv("APP_RELOAD", "false").lower() in ("true", "1", "t")

DEVICE_COMMAND_CHANNEL = os.getenv("DEVICE_COMMAND_CHANNEL", "device_commands")


USE_REDIS_SENTINEL = os.getenv("USE_REDIS_SENTINEL", "false").lower() in ("true", "1", "t")
REDIS_SENTINELS = os.getenv("REDIS_SENTINELS", "redis-sentinel:26379")
REDIS_MASTER_NAME = os.getenv("REDIS_MASTER_NAME", "mymaster")
