# IOTdeviceSim (IoT Device Simulator)

A lightweight **FastAPI** application that simulates IoT devices and exposes REST APIs for device management and command handling.

The project includes an **async pytest test suite** with automatic **HTML and JUnit reports**, a **Redis backend**, and a **GitHub Actions CI pipeline** for continuous testing.

---

## Tech Stack

* Python 3.11
* FastAPI
* Redis
* Pytest + pytest-asyncio
* Docker & Docker Compose
* GitHub Actions (CI)

---

## Project Structure

```
IOTdeviceSim/
│
├── src/
│   ├── app.py                # FastAPI application entrypoint
│   ├── config.py             # Configuration & environment variables
│   ├── dependencies.py       # Shared dependencies (Redis, etc.)
│   ├── models.py             # Pydantic models / schemas
│   ├── utils.py              # Helper utilities
│   ├── test_devices.json     # Sample devices data (seeding)
│   └── tests/                # Automated pytest test suite
│
├── docker-compose.yml        # Runs app + Redis
├── dockerfile                # Application container definition
├── pytest.ini                # Pytest configuration & reporting
├── reports/                  # Test reports (HTML, JUnit)
├── requirements.txt
└── README.md
```

---

## Running the Application

### Option A: Run with Docker Compose (Recommended)

```bash
docker compose up --build
```

Application will be available at:

* API: [http://localhost:8008](http://localhost:8008)
* Swagger UI: [http://localhost:8008/docs](http://localhost:8008/docs)
* ReDoc: [http://localhost:8008/redoc](http://localhost:8008/redoc)

Stop services:

```bash
docker compose down
```

#### Redis connection (Docker)

```
REDIS_HOST=redis
REDIS_PORT=6379
```

---

### Option B: Run Locally (Without Docker)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.app:app --reload --host 0.0.0.0 --port 8008
```

If Redis runs locally:

```
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Redis Pub/Sub

The application uses **Redis Pub/Sub** to publish device commands and process them asynchronously via a background listener.

### Channels

* **Command channel**: `device_commands`

  * Used to publish device command events
  * Listener subscribes to this channel on application startup

---

### Redis CLI Access (Docker)

```bash
docker exec -it <redis_container_name> redis-cli
```

Example:

```bash
docker exec -it relaxed_meitner redis-cli
```

---

### Pub/Sub Commands

**Publish a command (manual test)**

```bash
PUBLISH device_commands '{"device_id": "1", "command": "reboot"}'
```

Expected output:

```
(integer) 1
```

`1` means one active subscriber received the message.

**Subscribe to the channel (manual listener)**

```bash
SUBSCRIBE device_commands
```

**Check active Pub/Sub channels**

```bash
PUBSUB CHANNELS
```

**Check number of subscribers**

```bash
PUBSUB NUMSUB device_commands
```

---

## Running the Tests

Run the full test suite locally:

```bash
pytest
```

### Test Reports

* HTML report: `reports/pytest_report.html`
* JUnit report: `reports/junit.xml`

The test suite includes:

* API tests
* Edge cases
* Swagger / OpenAPI validation
* Performance benchmarks
* Redis integration tests

---

## Continuous Integration (CI)

The project uses **GitHub Actions** to automatically run the test suite on:

* Every push to `main` / `master`
* Every pull request

### CI Features

* Spins up Redis using GitHub Actions services
* Installs Python dependencies
* Runs the full pytest suite
* Fails the build on any test failure
* Provides logs and test results per run

CI configuration file:

```
.github/workflows/tests.yml
```

CI status and logs can be viewed under the **Actions** tab in GitHub.

---

## Assumptions and Design Choices

* Redis is required for device state, history, and command processing
* Docker Compose is the recommended runtime environment
* Redis Pub/Sub is used for asynchronous command handling
* The application listens on port **8008**
* CI ensures code quality and test stability on every change
