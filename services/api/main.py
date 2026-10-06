"""TaskForge API: accepts jobs, pushes them to a Redis queue, exposes status + Prometheus metrics."""
import json
import logging
import os
import time
import uuid

import redis
from fastapi import Depends, FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field

QUEUE = "taskforge:queue"
RECENT = "taskforge:recent"

logging.basicConfig(level=logging.INFO, format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("api")

app = FastAPI(title="TaskForge API", version=os.getenv("APP_VERSION", "dev"))
JOBS_SUBMITTED = Counter("taskforge_jobs_submitted_total", "Jobs submitted", ["type"])
QUEUE_LENGTH = Gauge("taskforge_queue_length", "Jobs waiting in queue")

_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    return _client


class JobIn(BaseModel):
    type: str = Field(pattern="^(hash|sleep|wordcount)$")
    payload: str = Field(default="", max_length=10000)


@app.get("/healthz")
def healthz(r=Depends(get_redis)):
    try:
        r.ping()
    except redis.RedisError:
        raise HTTPException(503, "redis unavailable")
    return {"status": "ok", "version": app.version}


@app.post("/api/jobs", status_code=201)
def submit(job: JobIn, r=Depends(get_redis)):
    job_id = uuid.uuid4().hex[:12]
    record = {"id": job_id, "type": job.type, "payload": job.payload, "status": "queued",
              "result": "", "created": str(int(time.time()))}
    r.hset(f"job:{job_id}", mapping=record)
    r.lpush(RECENT, job_id)
    r.ltrim(RECENT, 0, 49)
    r.rpush(QUEUE, job_id)
    JOBS_SUBMITTED.labels(job.type).inc()
    log.info("job submitted id=%s type=%s", job_id, job.type)
    return record


@app.get("/api/jobs")
def list_jobs(r=Depends(get_redis)):
    return [j for j in (r.hgetall(f"job:{i}") for i in r.lrange(RECENT, 0, 19)) if j]


@app.get("/api/stats")
def stats(r=Depends(get_redis)):
    jobs = [j for j in (r.hgetall(f"job:{i}") for i in r.lrange(RECENT, 0, 49)) if j]
    counts = {k: sum(1 for j in jobs if j.get("status") == k) for k in ("queued", "processing", "done", "failed")}
    return {"queue_length": r.llen(QUEUE), "recent_total": len(jobs), **counts, "version": app.version}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, r=Depends(get_redis)):
    job = r.hgetall(f"job:{job_id}")
    if not job:
        raise HTTPException(404, "job not found")
    return job


@app.get("/metrics")
def metrics(r=Depends(get_redis)):
    QUEUE_LENGTH.set(r.llen(QUEUE))
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
