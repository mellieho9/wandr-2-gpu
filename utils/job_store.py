import redis
import json
from typing import Dict, Optional

from config.settings import settings


class JobStore:
    """In-memory or Redis-backed job storage"""

    def __init__(self):
        if settings.REDIS_HOST:
            # Use Redis for production
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
            )
            self.use_redis = True
        else:
            # Use in-memory dict for local dev
            self.jobs = {}
            self.use_redis = False

    def create_job(self, job_id: str, data: Dict):
        """Create new job"""
        if self.use_redis:
            self.redis_client.setex(
                f"job:{job_id}",
                3600,  # 1 hour TTL
                json.dumps(data),
            )
        else:
            self.jobs[job_id] = data

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        if self.use_redis:
            data = self.redis_client.get(f"job:{job_id}")
            return json.loads(data) if data else None
        else:
            return self.jobs.get(job_id)

    def update_job(self, job_id: str, updates: Dict):
        """Update job data"""
        job = self.get_job(job_id)
        if job:
            job.update(updates)

            if self.use_redis:
                self.redis_client.setex(f"job:{job_id}", 3600, json.dumps(job))
            else:
                self.jobs[job_id] = job
