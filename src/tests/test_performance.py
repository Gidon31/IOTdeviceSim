def test_benchmark_get_devices_empty(app_client, benchmark):
    def run():
        r = app_client.get("/devices")
        assert r.status_code == 200

    benchmark.pedantic(run, rounds=30, warmup_rounds=5)

async def test_benchmark_get_devices_populated(app_client, populated_devices, benchmark):
    def run():
        r = app_client.get("/devices")
        assert r.status_code == 200

    benchmark.pedantic(run, rounds=40, warmup_rounds=5)

async def test_benchmark_send_command(app_client, redis_client, benchmark):
    device_id = "1"
    await redis_client.hset(f"device:{device_id}", mapping={"status": "normal", "online": "true"})

    payload = {"status": "normal"}

    def run():
        r = app_client.post(f"/devices/{device_id}/command", json=payload)
        assert r.status_code == 200

    benchmark.pedantic(run, rounds=30, warmup_rounds=5)

def test_get_devices_returns_fast_enough(app_client, benchmark):
    def run():
        r = app_client.get("/devices")
        assert r.status_code == 200

    benchmark(run)

def test_benchmark_get_device_not_found(app_client, benchmark):
    def run():
        r = app_client.get("/devices/does-not-exist")
        assert r.status_code == 404

    benchmark.pedantic(run, rounds=50, warmup_rounds=10)

    stats = benchmark.stats.stats
    assert stats.median < 0.03
    assert stats.max < 0.08