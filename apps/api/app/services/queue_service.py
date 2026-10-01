import asyncio
import json
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.config import get_settings
from app.core.logging import logger
from app.schemas.job import JobProgressEvent

settings = get_settings()


class QueueService:
    """Manages asynchronous job state, dispatch queues, and PubSub progress broadcasting."""

    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._memory_jobs: dict[str, JobProgressEvent] = {}
        self._memory_subscribers: dict[str, list[asyncio.Queue]] = {}

    async def get_redis(self) -> aioredis.Redis | None:
        if self._redis is None:
            try:
                r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await asyncio.wait_for(r.ping(), timeout=2.0)
                self._redis = r
                logger.info(f"Connected to Redis Queue at {settings.REDIS_URL}")
            except (TimeoutError, aioredis.RedisError, OSError) as exc:
                logger.warning(f"Redis unavailable ({exc}). Using in-memory job queue and pubsub.")
                self._redis = None
        return self._redis

    async def save_job_state(self, job_event: JobProgressEvent) -> None:
        """Saves current job progress state in Redis / Memory and broadcasts update."""
        jid = job_event.job_id
        self._memory_jobs[jid] = job_event

        # Broadcast in-memory subscribers
        if jid in self._memory_subscribers:
            for q in self._memory_subscribers[jid]:
                await q.put(job_event)

        # Broadcast via Redis PubSub if available
        r = await self.get_redis()
        if r:
            try:
                payload = json.dumps(job_event.model_dump())
                await r.set(f"job:{jid}:state", payload, ex=settings.DOWNLOAD_EXPIRY_SECONDS)
                await r.publish(f"job:{jid}:events", payload)
            except (aioredis.RedisError, OSError) as exc:
                logger.error(f"Redis publish error: {exc}")

    async def get_job_state(self, job_id: str) -> JobProgressEvent | None:
        """Retrieves current job state."""
        r = await self.get_redis()
        if r:
            try:
                data = await r.get(f"job:{job_id}:state")
                if data:
                    return JobProgressEvent(**json.loads(data))
            except (aioredis.RedisError, json.JSONDecodeError, OSError) as exc:
                logger.debug(f"Redis read error: {exc}")
        return self._memory_jobs.get(job_id)

    async def subscribe_events(self, job_id: str) -> AsyncGenerator[JobProgressEvent, None]:
        """Asynchronous generator streaming real-time progress events for a job."""
        # Yield current initial state
        initial = await self.get_job_state(job_id)
        if initial:
            yield initial

        # Local Queue for subscriber
        q: asyncio.Queue[JobProgressEvent] = asyncio.Queue()
        if job_id not in self._memory_subscribers:
            self._memory_subscribers[job_id] = []
        self._memory_subscribers[job_id].append(q)

        try:
            while True:
                event = await q.get()
                yield event
                if event.status in ("COMPLETED", "FAILED", "CANCELLED", "EXPIRED"):
                    break
        finally:
            if job_id in self._memory_subscribers and q in self._memory_subscribers[job_id]:
                self._memory_subscribers[job_id].remove(q)


queue_service = QueueService()
