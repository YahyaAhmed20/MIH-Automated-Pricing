import json

import redis
from django.conf import settings


class ProgressService:
    KEY = "system_update_progress"

    DEFAULT = {
        "completed": 0,
        "total": 16,
        "current_command": "",
        "is_running": False,
        "results": [],
    }

    @classmethod
    def redis(cls):
        return redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
        )

    @classmethod
    def get(cls):
        data = cls.redis().get(cls.KEY)

        if not data:
            return cls.DEFAULT.copy()

        return json.loads(data)

    @classmethod
    def save(cls, data):
        cls.redis().set(
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