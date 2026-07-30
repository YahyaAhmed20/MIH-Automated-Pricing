import json

import redis
from django.conf import settings


class ProgressService:
    KEY = "system_update_progress"

    DEFAULT = {
        "completed": 0,
        "total": 18,
        "current_command": "",
        "is_running": False,
        "results": [],
    }

    @classmethod
    def redis(cls):
        redis_url = settings.CELERY_BROKER_URL

        if not redis_url:
            return None

        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
        )

    @classmethod
    def get(cls):
        client = cls.redis()

        if client is None:
            return cls.DEFAULT.copy()

        data = client.get(cls.KEY)

        if not data:
            return cls.DEFAULT.copy()

        return json.loads(data)

    @classmethod
    def save(cls, data):
        client = cls.redis()

        if client is None:
            return

        client.set(
            cls.KEY,
            json.dumps(data),
        )

    @classmethod
    def reset(cls):
        cls.save(cls.DEFAULT.copy())

    @classmethod
    def update(cls, **kwargs):
        data = cls.get()

        data.update(kwargs)

        cls.save(data)

        return data