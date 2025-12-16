# IOTdeviceSim (IoT Device Simulator)

A lightweight **FastAPI** application that simulates IoT devices and exposes REST APIs for device management and command handling.  
The project includes an **async pytest** test suite with automatic HTML and JUnit reporting, and a **Docker Compose** setup with Redis.

---

## Tech Stack

- Python 3.11
- FastAPI
- Redis
- Pytest + pytest-asyncio
- Docker & Docker Compose

---

## Project Structure

```text
IOTdeviceSim/
│
├── src/
│   ├── app.py                # FastAPI application entrypoint
│   ├── config.py             # Configuration
│   ├── dependencies.py       # Shared dependencies
│   ├── models.py             # Pydantic models / schemas
│   ├── utils.py              # Helper utilities
│   ├── test_devices.json     # Sample devices data (seeding)
│   └── tests/                # Automated pytest suite
│
├── docker-compose.yml        # Runs app + redis
├── dockerfile                # Application container definition
├── pytest.ini                # Pytest configuration and reporting
├── reports/                  # Test reports
├── requirements.txt
└── README.md
```

---

## Running the Application

### Option A: Run with Docker Compose (recommended)

```bash
docker compose up --build
```

Application will be available at:

- API: http://localhost:8008  
- Swagger UI: http://localhost:8008/docs  
- ReDoc: http://localhost:8008/redoc  

Stop services:
```bash
docker compose down
```

### Redis connection (Docker)

```env
REDIS_HOST=redis
REDIS_PORT=6379
```

---

### Option B: Run locally (without Docker)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.app:app --reload --host 0.0.0.0 --port 8008
```

If Redis runs locally:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Redis Pub/Sub

The application uses **Redis Pub/Sub** to publish device commands and process them asynchronously via a background listener.

### Channel

- **Command channel:** `device_commands`
- Used to publish device command events
- Listener subscribes to this channel on application startup

---

## Redis CLI Access (Docker)

```bash
docker exec -it <redis_container_name> redis-cli
```

Example:
```bash
docker exec -it relaxed_meitner redis-cli
```

---

## Pub/Sub Commands

### Publish a command (manual test)

```bash
PUBLISH device_commands '{"device_id": "1", "command": "reboot"}'
```

Expected output:
```text
(integer) 1
```

> `(integer) 1` means one active subscriber received the message.

---

### Subscribe to the channel (manual listener)

```bash
SUBSCRIBE device_commands
```

---

### Check active Pub/Sub channels

```bash
PUBSUB CHANNELS
```

---

### Check number of subscribers for a channel

```bash
PUBSUB NUMSUB device_commands
```

---

### Check number of pattern subscribers

```bash
PUBSUB NUMPAT
```

---

## Running the Tests

```bash
pytest
```

Reports:
- HTML: reports/pytest_report.html
- JUnit: reports/junit.xml

---

## Assumptions and Design Choices

- Redis is required for device state and command processing
- Docker Compose is the recommended setup
- The application listens on port **8008**
