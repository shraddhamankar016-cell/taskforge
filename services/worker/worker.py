"""TaskForge worker: pulls jobs from Redis, processes them, exposes Prometheus metrics on :8001."""
import hashlib
import logging
import os
import signal
import time

import redis
from prometheus_client import Counter, Histogram, start_http_server

QUEUE = "taskforge:queue"
logging.basicConfig(level=logging.INFO, format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("worker")

PROCESSED = Counter("taskforge_jobs_processed_total", "Jobs processed", ["type", "status"])
DURATION = Histogram("taskforge_job_duration_seconds", "Job duration", ["type"])
running = True


def stop(*_):
    global running
    running = False
    log.info("shutdown signal received, finishing current job")


def process(job_type: str, payload: str) -> str:
    if job_type == "hash":
        return hashlib.sha256(payload.encode()).hexdigest()
    if job_type == "wordcount":
        return str(len(payload.split()))
    if job_type == "sleep":
        secs = min(int(payload or 3), 10)
        time.sleep(secs)
        return f"slept {secs}s"
    raise ValueError(f"unknown job type {job_type}")


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    start_http_server(8001)
    log.info("worker started")
    while running:
        item = r.blpop(QUEUE, timeout=3)
        if not item:
            continue
        job_id = item[1]
        job = r.hgetall(f"job:{job_id}")
        if not job:
            continue
        r.hset(f"job:{job_id}", "status", "processing")
        start = time.time()
        try:
            result, status = process(job["type"], job.get("payload", "")), "done"
        except Exception as exc:  # noqa: BLE001
            result, status = str(exc), "failed"
        DURATION.labels(job["type"]).observe(time.time() - start)
        PROCESSED.labels(job["type"], status).inc()
        r.hset(f"job:{job_id}", mapping={"status": status, "result": result})
        log.info("job %s %s", job_id, status)


if __name__ == "__main__":
    main()
