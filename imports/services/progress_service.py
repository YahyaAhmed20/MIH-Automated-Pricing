import json
import time
import redis

from celery import current_app

from django.conf import settings
from django.utils import timezone
from redis.exceptions import TimeoutError as RedisTimeoutError, ConnectionError


class ProgressService:

    KEY = "system_update_progress"
    LAST_SUCCESSFUL_UPDATE_KEY = "system_update_last_successful_update"

    # لو مفيش heartbeat لمدة 60 ثانية نعتبر الـ worker فقدناه
    HEARTBEAT_TIMEOUT = 60

    QUEUED_TIMEOUT = 180  # 3 دقائق

    # Distributed lock لمنع تشغيل أكثر من Update في نفس الوقت
    LOCK_KEY = "system_update_lock"
    LOCK_TTL = 7200  # ساعتان كحد أقصى، والـ heartbeat يجدده

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
    # Distributed Lock
    # ================================================================

    @classmethod
    def acquire_lock(cls, task_id, ttl=None):
        """
        محاولة امتلاك Lock للتحديث.
        Task واحد فقط يستطيع امتلاك الـ Lock.
        """
        client = cls.redis()

        if client is None:
            raise RuntimeError("Redis is unavailable")

        ttl = ttl or cls.LOCK_TTL

        return bool(
            client.set(
                cls.LOCK_KEY,
                task_id,
                nx=True,
                ex=ttl,
            )
        )

    @classmethod
    def owns_lock(cls, task_id):
        """
        التحقق أن الـ Lock الحالي مملوك لهذا الـ Task.
        """
        client = cls.redis()

        if client is None:
            return False

        try:
            return client.get(cls.LOCK_KEY) == task_id
        except Exception:
            return False

    @classmethod
    def refresh_lock(cls, task_id):
        """
        تجديد مدة الـ Lock بشرط أن يكون مملوكًا لنفس الـ Task.
        """
        client = cls.redis()

        if client is None:
            return False

        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("EXPIRE", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        try:
            return bool(
                client.eval(
                    script,
                    1,
                    cls.LOCK_KEY,
                    task_id,
                    cls.LOCK_TTL,
                )
            )
        except Exception as exc:
            print(
                f"⚠️ ProgressService.refresh_lock: {exc}"
            )
            return False

    @classmethod
    def release_lock(cls, task_id):
        """
        تحرير الـ Lock فقط إذا كان مملوكًا لهذا الـ Task.
        """
        client = cls.redis()

        if client is None:
            return False

        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        try:
            return bool(
                client.eval(
                    script,
                    1,
                    cls.LOCK_KEY,
                    task_id,
                )
            )
        except Exception as exc:
            print(
                f"❌ ProgressService.release_lock: {exc}"
            )
            return False

    @classmethod
    def is_task_alive(cls, task_id):
        """
        التحقق مما إذا كانت الـ Task موجودة فعليًا داخل Celery worker.

        نبحث في:
        - active
        - reserved
        - scheduled

        مهم:
        عدم العثور على الـ Task لا يعني وحده أنها ماتت،
        لذلك الدالة تُستخدم فقط كجزء من stale detection.
        """

        if not task_id:
            return False

        try:
            inspect = current_app.control.inspect(
                timeout=3.0
            )

            active = inspect.active()
            reserved = inspect.reserved()
            scheduled = inspect.scheduled()

            # عدم القدرة على الوصول إلى Worker ≠ عدم وجود Task
            if active is None or reserved is None or scheduled is None:
                return None

            active = active or {}
            reserved = reserved or {}
            scheduled = scheduled or {}

            for tasks in active.values():
                for task in tasks or []:
                    if task.get("id") == task_id:
                        return True

            for tasks in reserved.values():
                for task in tasks or []:
                    if task.get("id") == task_id:
                        return True

            for tasks in scheduled.values():
                for item in tasks or []:
                    request = item.get("request", {})
                    if request.get("id") == task_id:
                        return True

            return False

        except Exception as exc:
            print(
                f"⚠️ ProgressService.is_task_alive: {exc}"
            )
            return None

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
    def get_or_raise(cls):
        """
        الحصول على حالة التحديث من Redis.

        بخلاف get():
        لا نحول فشل Redis إلى حالة idle،
        لأن ذلك قد يؤدي إلى تشغيل Update جديد
        بينما يوجد Task فعلي شغال.
        """

        client = cls.redis()

        if client is None:
            raise RuntimeError("Redis is unavailable")

        try:
            data = client.get(cls.KEY)

            if not data:
                return cls.DEFAULT.copy()

            parsed = json.loads(data)

            if not isinstance(parsed, dict):
                raise RuntimeError("Invalid progress data in Redis")

            return parsed

        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            raise RuntimeError(
                f"Invalid progress data in Redis: {exc}"
            ) from exc

        except (RedisTimeoutError, ConnectionError) as exc:
            raise RuntimeError(
                f"Redis connection error: {exc}"
            ) from exc

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
    def update(cls, task_id=None, **kwargs):
        """
        تحديث جزء من حالة التحديث.

        إذا تم تمرير task_id:
        - يجب أن يكون هو صاحب الـTask الحالي.
        - يجب أن يمتلك Distributed Lock.
        - فشل Redis لا يتحول إلى DEFAULT/idle.
        """

        try:
            data = (
                cls.get_or_raise()
                if task_id is not None
                else cls.get()
            )

            if task_id is not None:

                current_task_id = data.get("task_id")

                if current_task_id != task_id:
                    print(
                        "⚠️ ProgressService.update: "
                        f"Task ownership mismatch. "
                        f"current={current_task_id}, "
                        f"requested={task_id}"
                    )
                    return None

                if not cls.owns_lock(task_id):
                    print(
                        "⚠️ ProgressService.update: "
                        f"Task {task_id} does not own the lock"
                    )
                    return None

            data.update(kwargs)

            if not cls.save(data):
                print(
                    "❌ ProgressService.update: "
                    "Failed to save progress"
                )
                return None

            return data

        except Exception as e:
            print(
                f"❌ ProgressService.update: {e}"
            )

            # مهم:
            # لا نرجع DEFAULT هنا عندما يكون هناك Task محدد.
            if task_id is not None:
                raise

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

        الـTask يجب أن يكون قد امتلك Distributed Lock
        قبل استدعاء هذه الدالة.
        """

        try:
            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.mark_queued: "
                    f"Task {task_id} does not own the lock"
                )
                return None

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

            if not cls.save(data):
                print(
                    "❌ ProgressService.mark_queued: "
                    "Failed to save queued state"
                )
                return None

            print(
                f"📥 ProgressService: "
                f"Task queued: {task_id}"
            )

            return data

        except Exception as e:
            print(
                f"❌ ProgressService.mark_queued: {e}"
            )
            return None

    # ================================================================
    # RUNNING
    # ================================================================

    @classmethod
    def mark_running(
        cls,
        task_id,
        update_type=None,
        total=None,
    ):
        """
        تحويل الـTask من queued إلى running.

        لا يسمح بالبدء إلا للـTask الذي:
        1. يطابق task_id المسجل في Progress.
        2. يمتلك Distributed Lock.
        """

        try:
            data = cls.get_or_raise()

            current_task_id = data.get("task_id")

            if current_task_id != task_id:
                print(
                    "⚠️ ProgressService.mark_running: "
                    f"Task ownership mismatch. "
                    f"current={current_task_id}, "
                    f"requested={task_id}"
                )
                return None

            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.mark_running: "
                    f"Task {task_id} does not own the lock"
                )
                return None

            now = timezone.localtime().isoformat()

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

            if not cls.save(data):
                print(
                    "❌ ProgressService.mark_running: "
                    "Failed to save running state"
                )
                return None

            # نبدأ دورة الـLock من جديد بعد بدء الـWorker
            if not cls.refresh_lock(task_id):
                print(
                    "❌ ProgressService.mark_running: "
                    f"Failed to refresh lock for {task_id}"
                )
                return None

            print(
                f"▶ ProgressService: "
                f"Task started: {task_id}"
            )

            return data

        except Exception as e:
            print(
                f"❌ ProgressService.mark_running: {e}"
            )
            return None

    # ================================================================
    # HEARTBEAT
    # ================================================================

    @classmethod
    def heartbeat(cls, task_id):
        """
        تحديث heartbeat وتجديد Distributed Lock.

        لا يسمح إلا للـTask صاحب الـLock بتحديث الحالة.
        """

        try:
            data = cls.get_or_raise()

            # التأكد أن الـTask الحالي هو صاحب العملية
            if data.get("task_id") != task_id:
                print(
                    "⚠️ ProgressService.heartbeat: "
                    f"Task ownership mismatch. "
                    f"current={data.get('task_id')}, "
                    f"requested={task_id}"
                )
                return False

            # التأكد أن الـTask ما زال يملك الـLock
            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.heartbeat: "
                    f"Task {task_id} no longer owns the lock"
                )
                return False

            # لا نعمل heartbeat إلا أثناء running
            if data.get("status") != "running":
                return False

            now = timezone.localtime().isoformat()

            data["heartbeat_at"] = now

            if not cls.save(data):
                print(
                    "⚠️ ProgressService.heartbeat: "
                    "Failed to save heartbeat"
                )
                return False

            # تجديد الـLock
            if not cls.refresh_lock(task_id):
                print(
                    "⚠️ ProgressService.heartbeat: "
                    f"Failed to refresh lock for {task_id}"
                )
                return False

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
        تحديد ما إذا كانت مهمة التحديث RUNNING عالقة فعلًا.

        لا يكفي أن يكون heartbeat قديمًا؛
        نتحقق أيضًا من حالة Celery Task.
        """

        try:
            data = cls.get_or_raise()

            if data.get("status") != "running":
                return False

            task_id = data.get("task_id")

            if not task_id:
                return True

            heartbeat_at = data.get("heartbeat_at")

            # لا يوجد heartbeat أصلًا
            if not heartbeat_at:
                heartbeat_stale = True
            else:
                heartbeat_time = timezone.datetime.fromisoformat(
                    heartbeat_at
                )

                if timezone.is_naive(heartbeat_time):
                    heartbeat_time = timezone.make_aware(
                        heartbeat_time,
                        timezone.get_current_timezone(),
                    )

                age = (
                    timezone.now() - heartbeat_time
                ).total_seconds()

                heartbeat_stale = age > cls.HEARTBEAT_TIMEOUT

            # إذا كان الـheartbeat ما زال حديثًا، فلا توجد مشكلة.
            if not heartbeat_stale:
                return False

            # ------------------------------------------------------------
            # heartbeat قديم → نتحقق من Celery
            # ------------------------------------------------------------

            task_alive = cls.is_task_alive(task_id)

            # Inspector لم يستطع الوصول إلى الـ Worker.
            # لا نغامر بعمل reset.
            if task_alive is None:
                return False

            # الـ Task موجودة فعليًا داخل أحد الـ Workers.
            if task_alive:
                return False

            # الـ Task غير موجودة في active/reserved/scheduled
            # والـ heartbeat قديم → العملية عالقة فعلًا.
            return True

        except Exception as exc:
            print(
                f"⚠️ ProgressService.is_stale: {exc}"
            )
            return False

    # ================================================================
    # RECOVERY
    # ================================================================

    @classmethod
    def recover_stale_update(cls):
        """
        استعادة Update عالقة سواء كانت QUEUED أو RUNNING.

        QUEUED:
            إذا لم تبدأ الـTask أصلًا ولم تعد موجودة في Celery،
            يتم اعتبارها orphaned ويتم تحرير الـLock.

        RUNNING:
            لا يتم Recovery إلا إذا كان heartbeat قديمًا
            والـTask غير موجودة في Celery.

        مهم:
            الـRecovery يتم بشكل Atomic، ولا يتم حذف Lock
            إذا تغيّر مالكه أثناء العملية.
        """

        try:
            data = cls.get_or_raise()

            status = data.get("status")
            task_id = data.get("task_id")

            # لا توجد عملية مرتبطة يمكن استعادتها
            if not task_id:
                return False

            # ============================================================
            # QUEUED RECOVERY
            # ============================================================

            if status == "queued":

                queued_at = data.get("queued_at")

                if not queued_at:
                    return False

                try:
                    queued_time = timezone.datetime.fromisoformat(
                        queued_at
                    )

                    if timezone.is_naive(queued_time):
                        queued_time = timezone.make_aware(
                            queued_time,
                            timezone.get_current_timezone(),
                        )

                    queued_age = (
                        timezone.now() - queued_time
                    ).total_seconds()

                except (TypeError, ValueError):
                    return False

                # لا نعتبر الـTask orphaned قبل مرور المهلة
                if queued_age < cls.QUEUED_TIMEOUT:
                    return False

                task_alive = cls.is_task_alive(task_id)

                # لا نستطيع التأكد من حالة Worker
                if task_alive is None:
                    return False

                # الـTask موجودة فعلًا → لا نلمسها
                if task_alive:
                    return False

                # --------------------------------------------------------
                # الـTask كانت QUEUED لكنها غير موجودة في Celery.
                # بما أنها لم تدخل RUNNING أصلًا، فهي orphaned.
                # --------------------------------------------------------

                now = timezone.localtime().isoformat()

                recovered_data = dict(data)

                recovered_data.update(
                    {
                        "status": "error",
                        "is_running": False,
                        "current_command": (
                            "⚠️ تم إنهاء التحديث السابق تلقائيًا "
                            "لأن Worker لم يبدأ المهمة."
                        ),
                        "finished_at": now,
                        "heartbeat_at": None,
                        "cancel_requested": False,
                        "error": (
                            "تم اكتشاف Update في حالة QUEUED "
                            "ولكن الـCelery Task لم تعد موجودة."
                        ),
                    }
                )

                client = cls.redis()

                if client is None:
                    raise RuntimeError("Redis is unavailable")

                # --------------------------------------------------------
                # Atomic Recovery
                # --------------------------------------------------------

                script = """
                if redis.call("GET", KEYS[1]) ~= ARGV[1] then
                    return 0
                end

                redis.call("SET", KEYS[2], ARGV[2], "EX", ARGV[3])
                redis.call("DEL", KEYS[1])

                return 1
                """

                result = client.eval(
                    script,
                    2,
                    cls.LOCK_KEY,
                    cls.KEY,
                    task_id,
                    json.dumps(
                        recovered_data,
                        ensure_ascii=False,
                    ),
                    3600,
                )

                if not result:
                    print(
                        "⚠️ ProgressService.recover_stale_update: "
                        "Lock ownership changed; recovery aborted"
                    )
                    return False

                print(
                    "♻️ ProgressService: "
                    f"Recovered orphaned queued update {task_id}"
                )

                return True

            # ============================================================
            # RUNNING RECOVERY
            # ============================================================

            if status == "running":

                # لا نستعيد RUNNING إلا إذا ثبت أنها stale
                if not cls.is_stale():
                    return False

                client = cls.redis()

                if client is None:
                    raise RuntimeError("Redis is unavailable")

                now = timezone.localtime().isoformat()

                recovered_data = dict(data)

                recovered_data.update(
                    {
                        "status": "error",
                        "is_running": False,
                        "current_command": (
                            "⚠️ تم إنهاء التحديث السابق تلقائيًا "
                            "لأن Worker فقد الاتصال."
                        ),
                        "finished_at": now,
                        "heartbeat_at": None,
                        "cancel_requested": False,
                        "error": (
                            "تم اكتشاف Update عالق بعد فقدان "
                            "Celery Worker."
                        ),
                    }
                )

                # --------------------------------------------------------
                # Atomic Recovery
                # --------------------------------------------------------

                script = """
                if redis.call("GET", KEYS[1]) ~= ARGV[1] then
                    return 0
                end

                redis.call("SET", KEYS[2], ARGV[2], "EX", ARGV[3])
                redis.call("DEL", KEYS[1])

                return 1
                """

                result = client.eval(
                    script,
                    2,
                    cls.LOCK_KEY,
                    cls.KEY,
                    task_id,
                    json.dumps(
                        recovered_data,
                        ensure_ascii=False,
                    ),
                    3600,
                )

                if not result:
                    print(
                        "⚠️ ProgressService.recover_stale_update: "
                        "Lock ownership changed; recovery aborted"
                    )
                    return False

                print(
                    "♻️ ProgressService: "
                    f"Recovered stale running update {task_id}"
                )

                return True

            # ============================================================
            # أي حالة أخرى لا تحتاج Recovery
            # ============================================================

            return False

        except Exception as exc:

            print(
                "❌ ProgressService.recover_stale_update: "
                f"{exc}"
            )

            return False

    # ================================================================
    # FINISHED
    # ================================================================

    @classmethod
    def mark_completed(cls, task_id, results=None, logs=None):
        """إنهاء التحديث بنجاح ثم تحرير الـLock."""

        try:
            data = cls.get_or_raise()

            if data.get("task_id") != task_id:
                print(
                    "⚠️ ProgressService.mark_completed: "
                    f"Task ownership mismatch. "
                    f"current={data.get('task_id')}, "
                    f"requested={task_id}"
                )
                return None

            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.mark_completed: "
                    f"Task {task_id} does not own the lock"
                )
                return None

            now = timezone.localtime().isoformat()

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

            if not cls.save(data):
                print(
                    "❌ ProgressService.mark_completed: "
                    "Failed to save completed state"
                )
                return None

            # تحرير الـLock بعد حفظ الحالة النهائية بنجاح
            cls.release_lock(task_id)

            return data

        except Exception as e:
            print(
                f"❌ ProgressService.mark_completed: {e}"
            )
            return None

    # ================================================================
    # ERROR
    # ================================================================

    @classmethod
    def mark_error(
        cls,
        task_id,
        message=None,
        logs=None,
        results=None,
    ):
        """إنهاء التحديث بخطأ ثم تحرير الـLock."""

        try:
            data = cls.get_or_raise()

            if data.get("task_id") != task_id:
                print(
                    "⚠️ ProgressService.mark_error: "
                    f"Task ownership mismatch. "
                    f"current={data.get('task_id')}, "
                    f"requested={task_id}"
                )
                return None

            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.mark_error: "
                    f"Task {task_id} does not own the lock"
                )
                return None

            now = timezone.localtime().isoformat()

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

            if not cls.save(data):
                print(
                    "❌ ProgressService.mark_error: "
                    "Failed to save error state"
                )
                return None

            # تحرير الـLock بعد حفظ الحالة النهائية بنجاح
            cls.release_lock(task_id)

            return data

        except Exception as e:
            print(
                f"❌ ProgressService.mark_error: {e}"
            )
            return None

    # ================================================================
    # CANCEL
    # ================================================================

    @classmethod
    def request_cancel(cls, task_id):
        """
        طلب إلغاء العملية الحالية مع التحقق من ملكية الـTask.

        Redis failure لا يُفسَّر على أنه عدم وجود Task.
        """

        try:
            data = cls.get_or_raise()

            if data.get("task_id") != task_id:
                print(
                    "⚠️ ProgressService.request_cancel: "
                    f"Task ownership mismatch. "
                    f"current={data.get('task_id')}, "
                    f"requested={task_id}"
                )
                return False

            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.request_cancel: "
                    f"Task {task_id} does not own the lock"
                )
                return False

            if data.get("status") not in ("queued", "running"):
                return False

            data["cancel_requested"] = True

            if not cls.save(data):
                print(
                    "❌ ProgressService.request_cancel: "
                    "Failed to save cancel request"
                )
                return False

            print(
                "🛑 ProgressService: "
                f"Cancel requested for task {task_id}"
            )

            return True

        except Exception as e:
            print(
                f"❌ ProgressService.request_cancel: {e}"
            )
            return False

    @classmethod
    def is_cancel_requested(cls, task_id):
        """
        التحقق من طلب الإلغاء للـTask الحالي.

        إذا تعذر الوصول إلى Redis، نرجع False فقط لأن
        هذه الدالة تُستدعى داخل Worker؛ والخطأ الحقيقي
        يجب أن يظهر في heartbeat/update التالي.
        """

        try:
            data = cls.get_or_raise()

            if data.get("task_id") != task_id:
                return False

            if not cls.owns_lock(task_id):
                return False

            return bool(
                data.get(
                    "cancel_requested",
                    False,
                )
            )

        except Exception as e:
            print(
                "⚠️ ProgressService.is_cancel_requested: "
                f"{e}"
            )
            return False

    @classmethod
    def clear_cancel(cls, task_id):
        """
        مسح طلب الإلغاء للـTask الحالي.
        """

        try:
            data = cls.get_or_raise()

            if data.get("task_id") != task_id:
                print(
                    "⚠️ ProgressService.clear_cancel: "
                    f"Task ownership mismatch. "
                    f"current={data.get('task_id')}, "
                    f"requested={task_id}"
                )
                return False

            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.clear_cancel: "
                    f"Task {task_id} does not own the lock"
                )
                return False

            data["cancel_requested"] = False

            if not cls.save(data):
                print(
                    "❌ ProgressService.clear_cancel: "
                    "Failed to clear cancel flag"
                )
                return False

            return True

        except Exception as e:
            print(
                f"❌ ProgressService.clear_cancel: {e}"
            )
            return False

    # ================================================================
    # CANCELLED
    # ================================================================

    @classmethod
    def mark_cancelled(cls, task_id, logs=None):
        """إنهاء العملية بسبب Cancel ثم تحرير الـLock."""

        try:
            data = cls.get_or_raise()

            if data.get("task_id") != task_id:
                print(
                    "⚠️ ProgressService.mark_cancelled: "
                    f"Task ownership mismatch. "
                    f"current={data.get('task_id')}, "
                    f"requested={task_id}"
                )
                return None

            if not cls.owns_lock(task_id):
                print(
                    "⚠️ ProgressService.mark_cancelled: "
                    f"Task {task_id} does not own the lock"
                )
                return None

            now = timezone.localtime().isoformat()

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

            if not cls.save(data):
                print(
                    "❌ ProgressService.mark_cancelled: "
                    "Failed to save cancelled state"
                )
                return None

            # تحرير الـLock بعد حفظ الحالة النهائية بنجاح
            cls.release_lock(task_id)

            return data

        except Exception as e:
            print(
                f"❌ ProgressService.mark_cancelled: {e}"
            )
            return None

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