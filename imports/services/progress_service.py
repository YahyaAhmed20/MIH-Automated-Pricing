import json
import time
import redis

from django.conf import settings
from django.utils import timezone
from redis.exceptions import TimeoutError as RedisTimeoutError, ConnectionError


class ProgressService:

    KEY = "system_update_progress"
    LAST_SUCCESSFUL_UPDATE_KEY = "system_update_last_successful_update"

    # لو مفيش heartbeat لمدة 60 ثانية نعتبر الـ worker فقدناه
    HEARTBEAT_TIMEOUT = 60

    DEFAULT = {
        "completed": 0,
        "total": 0,
        "current_command": "",
        "is_running": False,
        "results": [],
        "logs": None,

        # idle | queued | running | completed | cancelled | error
        "status": "idle",

        "cancel_requested": False,

        # معلومات الـTask
        "task_id": None,
        "update_type": None,

        # توقيتات التشغيل
        "queued_at": None,
        "started_at": None,
        "heartbeat_at": None,
        "finished_at": None,
    }

    # ================================================================
    # Redis
    # ================================================================

    @classmethod
    def redis(cls):
        """إنشاء اتصال Redis مع إعدادات Timeout محسّنة."""

        redis_url = settings.CELERY_BROKER_URL

        if not redis_url:
            return None

        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=30,
            socket_connect_timeout=30,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=10,
        )

    # ================================================================
    # Basic Get / Save
    # ================================================================

    @classmethod
    def get(cls):
        """الحصول على حالة التحديث الحالية من Redis."""

        client = cls.redis()

        if client is None:
            return cls.DEFAULT.copy()

        try:
            data = client.get(cls.KEY)

            if not data:
                return cls.DEFAULT.copy()

            parsed = json.loads(data)

            if not isinstance(parsed, dict):
                return cls.DEFAULT.copy()

            return parsed

        except (json.JSONDecodeError, TypeError, AttributeError) as e:

            print(
                f"⚠️ ProgressService.get: "
                f"Invalid progress data: {e}"
            )

            return cls.DEFAULT.copy()

        except (RedisTimeoutError, ConnectionError) as e:

            print(
                f"⚠️ ProgressService.get: "
                f"Redis connection error: {e}"
            )

            return cls.DEFAULT.copy()

    @classmethod
    def save(cls, data):
        """حفظ حالة التحديث في Redis."""

        client = cls.redis()

        if client is None:
            print(
                "⚠️ ProgressService.save: "
                "Redis client is None"
            )
            return False

        max_retries = 3

        for attempt in range(max_retries):

            try:

                client.set(
                    cls.KEY,
                    json.dumps(
                        data,
                        ensure_ascii=False,
                    ),
                    ex=3600,
                )

                return True

            except (RedisTimeoutError, ConnectionError) as e:

                if attempt < max_retries - 1:

                    wait_time = 2 ** attempt

                    print(
                        f"⚠️ ProgressService.save: "
                        f"Attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s: {e}"
                    )

                    time.sleep(wait_time)

                else:

                    print(
                        f"❌ ProgressService.save: "
                        f"Failed after {max_retries} attempts: {e}"
                    )

                    return False

            except Exception as e:

                print(
                    f"❌ ProgressService.save: "
                    f"Unexpected error: {e}"
                )

                return False

        return False

    # ================================================================
    # Reset
    # ================================================================

    @classmethod
    def reset(cls):
        """
        إعادة تعيين حالة التحديث فقط.

        لا يتم لمس:
        LAST_SUCCESSFUL_UPDATE_KEY
        """

        try:

            data = cls.DEFAULT.copy()

            cls.save(data)

            print(
                "✅ ProgressService: "
                "Progress data reset successfully"
            )

        except Exception as e:

            print(
                f"❌ ProgressService.reset: {e}"
            )

    # ================================================================
    # Generic Update
    # ================================================================

    @classmethod
    def update(cls, **kwargs):
        """تحديث جزء من حالة التحديث."""

        try:

            data = cls.get()

            data.update(kwargs)

            cls.save(data)

            return data

        except Exception as e:

            print(
                f"❌ ProgressService.update: {e}"
            )

            return cls.DEFAULT.copy()

    # ================================================================
    # QUEUED
    # ================================================================

    @classmethod
    def mark_queued(
        cls,
        task_id,
        update_type,
        total,
    ):
        """
        تسجيل أن الـTask تم وضعه في Celery Queue.

        مهم:
        هذه ليست running.
        """

        now = timezone.localtime().isoformat()

        data = cls.DEFAULT.copy()

        data.update(
            {
                "status": "queued",
                "is_running": False,

                "task_id": task_id,
                "update_type": update_type,

                "total": total,
                "completed": 0,

                "current_command": (
                    "⏳ في انتظار بدء Worker..."
                ),

                "logs": None,
                "results": [],

                "cancel_requested": False,

                "queued_at": now,
                "started_at": None,
                "heartbeat_at": None,
                "finished_at": None,
            }
        )

        cls.save(data)

        print(
            f"📥 ProgressService: "
            f"Task queued: {task_id}"
        )

        return data

    # ================================================================
    # RUNNING
    # ================================================================

    @classmethod
    def mark_running(
        cls,
        task_id=None,
        update_type=None,
        total=None,
    ):
        """
        يتم استدعاؤها من داخل Celery Task فقط.

        هنا فقط نعتبر أن التحديث بدأ فعليًا.
        """

        now = timezone.localtime().isoformat()

        data = cls.get()

        if task_id is not None:
            data["task_id"] = task_id

        if update_type is not None:
            data["update_type"] = update_type

        if total is not None:
            data["total"] = total

        data.update(
            {
                "status": "running",
                "is_running": True,

                "completed": 0,

                "current_command": (
                    "⏳ جاري تهيئة التحديث..."
                ),

                "cancel_requested": False,

                "started_at": now,
                "heartbeat_at": now,
                "finished_at": None,
            }
        )

        cls.save(data)

        print(
            f"▶ ProgressService: "
            f"Task started: {data.get('task_id')}"
        )

        return data

    # ================================================================
    # HEARTBEAT
    # ================================================================

    @classmethod
    def heartbeat(cls):
        """
        تحديث آخر وقت تم فيه التواصل مع الـWorker.

        يتم استدعاؤها أثناء تشغيل الـTask.
        """

        try:

            now = timezone.localtime().isoformat()

            data = cls.get()

            data["heartbeat_at"] = now

            cls.save(data)

            return True

        except Exception as e:

            print(
                f"⚠️ ProgressService.heartbeat: {e}"
            )

            return False

    # ================================================================
    # STALE CHECK
    # ================================================================

    @classmethod
    def is_stale(cls):
        """
        معرفة إذا كان الـWorker توقف عن إرسال heartbeat.

        لا نعتبر queued stale بنفس الطريقة.
        """

        try:

            data = cls.get()

            if data.get("status") != "running":
                return False

            heartbeat_at = data.get("heartbeat_at")

            if not heartbeat_at:
                return True

            heartbeat_time = timezone.datetime.fromisoformat(
                heartbeat_at
            )

            if timezone.is_naive(heartbeat_time):
                heartbeat_time = timezone.make_aware(
                    heartbeat_time,
                    timezone.get_current_timezone(),
                )

            now = timezone.now()

            age = (
                now - heartbeat_time
            ).total_seconds()

            return age > cls.HEARTBEAT_TIMEOUT

        except Exception as e:

            print(
                f"⚠️ ProgressService.is_stale: {e}"
            )

            return False

    # ================================================================
    # FINISHED
    # ================================================================

    @classmethod
    def mark_completed(
        cls,
        results=None,
        logs=None,
    ):
        """إنهاء التحديث بنجاح."""

        now = timezone.localtime().isoformat()

        data = cls.get()

        data.update(
            {
                "status": "completed",
                "is_running": False,

                "current_command": (
                    "✅ تم الانتهاء من التحديث بنجاح!"
                ),

                "finished_at": now,
                "heartbeat_at": now,
                "cancel_requested": False,
            }
        )

        if results is not None:
            data["results"] = results

        if logs is not None:
            data["logs"] = logs

        cls.save(data)

        return data

    # ================================================================
    # ERROR
    # ================================================================

    @classmethod
    def mark_error(
        cls,
        message=None,
        logs=None,
        results=None,
    ):
        """إنهاء التحديث مع وجود خطأ."""

        now = timezone.localtime().isoformat()

        data = cls.get()

        data.update(
            {
                "status": "error",
                "is_running": False,

                "current_command": (
                    "❌ حدث خطأ أثناء التحديث"
                ),

                "finished_at": now,
                "heartbeat_at": now,
                "cancel_requested": False,
            }
        )

        if message:
            data["error"] = str(message)

        if logs is not None:
            data["logs"] = logs

        if results is not None:
            data["results"] = results

        cls.save(data)

        return data

    # ================================================================
    # CANCEL
    # ================================================================

    @classmethod
    def request_cancel(cls):
        """طلب إلغاء العملية الحالية."""

        try:

            data = cls.get()

            if data.get("status") not in (
                "queued",
                "running",
            ):
                return False

            data["cancel_requested"] = True

            cls.save(data)

            print(
                "🛑 ProgressService: "
                "Cancel requested"
            )

            return True

        except Exception as e:

            print(
                f"❌ ProgressService.request_cancel: {e}"
            )

            return False

    @classmethod
    def is_cancel_requested(cls):
        """التحقق من طلب الإلغاء."""

        try:

            return bool(
                cls.get().get(
                    "cancel_requested",
                    False,
                )
            )

        except Exception as e:

            print(
                f"⚠️ ProgressService.is_cancel_requested: "
                f"{e}"
            )

            return False

    @classmethod
    def clear_cancel(cls):
        """مسح طلب الإلغاء."""

        try:

            cls.update(
                cancel_requested=False
            )

            print(
                "✅ ProgressService: "
                "Cancel flag cleared"
            )

        except Exception as e:

            print(
                f"❌ ProgressService.clear_cancel: {e}"
            )

    # ================================================================
    # CANCELLED
    # ================================================================

    @classmethod
    def mark_cancelled(
        cls,
        logs=None,
    ):
        """إنهاء العملية بسبب Cancel."""

        now = timezone.localtime().isoformat()

        data = cls.get()

        data.update(
            {
                "status": "cancelled",
                "is_running": False,

                "current_command": (
                    "🛑 تم إلغاء التحديث"
                ),

                "finished_at": now,
                "heartbeat_at": now,
                "cancel_requested": False,
            }
        )

        if logs is not None:
            data["logs"] = logs

        cls.save(data)

        return data

    # ================================================================
    # Status
    # ================================================================

    @classmethod
    def set_status(cls, status):
        """تعيين حالة العملية."""

        try:

            cls.update(
                status=status
            )

            print(
                f"✅ ProgressService: "
                f"Status set to '{status}'"
            )

        except Exception as e:

            print(
                f"❌ ProgressService.set_status: {e}"
            )

    # ================================================================
    # Logs
    # ================================================================

    @classmethod
    def clear_logs(cls):
        """مسح الـLogs فقط."""

        try:

            data = cls.get()

            data["logs"] = None

            cls.save(data)

            print(
                "✅ ProgressService: Logs cleared"
            )

        except Exception as e:

            print(
                f"❌ ProgressService.clear_logs: {e}"
            )

    @classmethod
    def reset_keep_logs(cls):
        """إعادة تعيين التقدم مع الاحتفاظ بالـLogs."""

        try:

            data = cls.get()

            current_logs = data.get("logs")

            cls.reset()

            if current_logs:
                cls.update(
                    logs=current_logs
                )

            print(
                "✅ ProgressService: "
                "Reset with logs preserved"
            )

        except Exception as e:

            print(
                f"❌ ProgressService.reset_keep_logs: {e}"
            )

    # ================================================================
    # Last Successful Update
    # ================================================================

    @classmethod
    def set_last_successful_update(
        cls,
        update_type="full",
    ):
        """
        حفظ وقت آخر تحديث ناجح.

        مستقل تمامًا عن Progress.
        """

        try:

            client = cls.redis()

            if client is None:

                print(
                    "⚠️ ProgressService."
                    "set_last_successful_update: "
                    "Redis client is None"
                )

                return None

            now = timezone.localtime()

            data = {
                "datetime": now.isoformat(),

                "display": now.strftime(
                    "%d/%m/%Y - %I:%M %p"
                ),

                "update_type": update_type,
            }

            client.set(
                cls.LAST_SUCCESSFUL_UPDATE_KEY,
                json.dumps(
                    data,
                    ensure_ascii=False,
                ),
            )

            print(
                "✅ Last successful update saved: "
                f"{data['display']} "
                f"({update_type})"
            )

            return data

        except (
            RedisTimeoutError,
            ConnectionError,
        ) as e:

            print(
                "⚠️ ProgressService."
                "set_last_successful_update: "
                f"Redis connection error: {e}"
            )

            return None

        except Exception as e:

            print(
                "❌ ProgressService."
                "set_last_successful_update: "
                f"Unexpected error: {e}"
            )

            return None

    @classmethod
    def get_last_successful_update(cls):
        """الحصول على آخر تحديث ناجح."""

        client = cls.redis()

        if client is None:
            return None

        try:

            data = client.get(
                cls.LAST_SUCCESSFUL_UPDATE_KEY
            )

            if not data:
                return None

            return json.loads(data)

        except (
            json.JSONDecodeError,
            TypeError,
            AttributeError,
        ) as e:

            print(
                "⚠️ ProgressService."
                "get_last_successful_update: "
                f"Invalid data: {e}"
            )

            return None

        except (
            RedisTimeoutError,
            ConnectionError,
        ) as e:

            print(
                "⚠️ ProgressService."
                "get_last_successful_update: "
                f"Redis connection error: {e}"
            )

            return None

        except Exception as e:

            print(
                "❌ ProgressService."
                "get_last_successful_update: "
                f"Unexpected error: {e}"
            )

            return None