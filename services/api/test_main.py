from fastapi.testclient import TestClient

from main import app, get_redis


class FakeRedis:
    def __init__(self):
        self.h, self.l = {}, {}

    def ping(self): return True
    def hset(self, k, mapping): self.h[k] = dict(mapping)
    def hgetall(self, k): return self.h.get(k, {})
    def lpush(self, k, v): self.l.setdefault(k, []).insert(0, v)
    def rpush(self, k, v): self.l.setdefault(k, []).append(v)
    def ltrim(self, k, a, b): self.l[k] = self.l.get(k, [])[a:b + 1]
    def lrange(self, k, a, b): return self.l.get(k, [])[a:b + 1]
    def llen(self, k): return len(self.l.get(k, []))


fake = FakeRedis()
app.dependency_overrides[get_redis] = lambda: fake
client = TestClient(app)


def test_health():
    assert client.get("/healthz").json()["status"] == "ok"


def test_submit_and_fetch():
    r = client.post("/api/jobs", json={"type": "hash", "payload": "hello"})
    assert r.status_code == 201
    job = client.get(f"/api/jobs/{r.json()['id']}").json()
    assert job["status"] == "queued"
    assert len(client.get("/api/jobs").json()) >= 1


def test_rejects_bad_type():
    assert client.post("/api/jobs", json={"type": "rm -rf", "payload": ""}).status_code == 422


def test_metrics():
    assert "taskforge_jobs_submitted_total" in client.get("/metrics").text


def test_stats():
    data = client.get("/api/stats").json()
    assert "queue_length" in data and "done" in data
