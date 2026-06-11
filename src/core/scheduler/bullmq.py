import logging
import json
import redis
from src.core.config import settings

logger = logging.getLogger(__name__)

class BullMQScheduler:
    """
    Simplified Python wrapper for BullMQ/Redis scheduling.
    Allows ARIA to schedule autonomous tasks.
    """
    def __init__(self):
        self.redis_conn = redis.from_url(settings.REDIS_URL)

    def schedule_task(self, queue_name: str, task_data: dict, delay_ms: int = 0):
        logger.info(f"Scheduling task on {queue_name} with delay {delay_ms}ms")
        job = {
            "name": "aria_task",
            "data": task_data,
            "opts": {"delay": delay_ms}
        }
        # BullMQ format for Redis
        self.redis_conn.lpush(f"bull:{queue_name}:id", json.dumps(job))
        return True

scheduler = BullMQScheduler()
