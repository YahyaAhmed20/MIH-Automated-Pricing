import json
import time
import redis
from django.conf import settings
from redis.exceptions import TimeoutError as RedisTimeoutError, ConnectionError


class ProgressService:
    KEY = "system_update_progress"

    DEFAULT = {
        "completed": 0,
        "total": 18,
        "current_command": "",
        "is_running": False,
        "results": [],
        "logs": None,
        "status": "idle",          # idle | running | completed | cancelled | error
        "cancel_requested": False,
    }

    @classmethod
    def redis(cls):
        """إنشاء اتصال Redis مع إعدادات Timeout محسّنة"""
        redis_url = settings.CELERY_BROKER_URL

        if not redis_url:
            return None

        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=30,           # 30 ثانية
            socket_connect_timeout=30,   # 30 ثانية
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=10,
        )

    @classmethod
    def get(cls):
        """الحصول على بيانات التقدم من Redis مع معالجة الأخطاء"""
        client = cls.redis()

        if client is None:
            return cls.DEFAULT.copy()

        try:
            data = client.get(cls.KEY)

            if not data:
                return cls.DEFAULT.copy()

            return json.loads(data)
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            # لو البيانات متخربشة أو مش موجودة، ارجع للـ DEFAULT
            print(f"⚠️ ProgressService.get: Error reading data, using default: {e}")
            return cls.DEFAULT.copy()
        except (RedisTimeoutError, ConnectionError) as e:
            # لو الـ Redis مش بيستجيب، ارجع للـ DEFAULT
            print(f"⚠️ ProgressService.get: Redis connection error, using default: {e}")
            return cls.DEFAULT.copy()

    @classmethod
    def save(cls, data):
        """حفظ بيانات التقدم في Redis مع إعادة المحاولة عند الفشل"""
        client = cls.redis()

        if client is None:
            print("⚠️ ProgressService.save: Redis client is None")
            return

        # ✅ حاول 3 مرات لو فشل
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client.set(
                    cls.KEY,
                    json.dumps(data),
                    ex=3600  # ساعة واحدة
                )
                return  # نجحت، اخرج من الدالة
            except (RedisTimeoutError, ConnectionError) as e:
                if attempt < max_retries - 1:  # لو مش آخر محاولة
                    wait_time = 2 ** attempt  # 1, 2, 4 ثواني
                    print(f"⚠️ ProgressService.save: Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    # آخر محاولة فشلت، سجل الخطأ
                    print(f"❌ ProgressService.save: Failed after {max_retries} attempts: {e}")
                    return
            except Exception as e:
                # أي خطأ غير متوقع
                print(f"❌ ProgressService.save: Unexpected error: {e}")
                return

    @classmethod
    def reset(cls):
        """إعادة تعيين بيانات التقدم"""
        try:
            cls.save(cls.DEFAULT.copy())
            print("✅ ProgressService: Progress data reset successfully")
        except Exception as e:
            print(f"❌ ProgressService: Failed to reset progress: {e}")

    @classmethod
    def update(cls, **kwargs):
        """تحديث بيانات التقدم"""
        try:
            data = cls.get()
            data.update(kwargs)
            cls.save(data)
            return data
        except Exception as e:
            print(f"❌ ProgressService.update: Failed to update: {e}")
            return cls.DEFAULT.copy()

    @classmethod
    def request_cancel(cls):
        """طلب إلغاء العملية"""
        try:
            cls.update(cancel_requested=True)
            print("✅ ProgressService: Cancel requested")
        except Exception as e:
            print(f"❌ ProgressService.request_cancel: Failed: {e}")

    @classmethod
    def is_cancel_requested(cls):
        """التحقق من وجود طلب إلغاء"""
        try:
            return cls.get().get("cancel_requested", False)
        except Exception as e:
            print(f"⚠️ ProgressService.is_cancel_requested: Failed: {e}")
            return False

    @classmethod
    def clear_cancel(cls):
        """مسح طلب الإلغاء"""
        try:
            cls.update(cancel_requested=False)
            print("✅ ProgressService: Cancel flag cleared")
        except Exception as e:
            print(f"❌ ProgressService.clear_cancel: Failed: {e}")

    @classmethod
    def set_status(cls, status):
        """تعيين حالة العملية"""
        try:
            cls.update(status=status)
            print(f"✅ ProgressService: Status set to '{status}'")
        except Exception as e:
            print(f"❌ ProgressService.set_status: Failed: {e}")

    @classmethod
    def clear_logs(cls):
        """مسح الـ Logs فقط مع الاحتفاظ بباقي البيانات"""
        try:
            data = cls.get()
            data['logs'] = None
            cls.save(data)
            print("✅ ProgressService: Logs cleared")
        except Exception as e:
            print(f"❌ ProgressService.clear_logs: Failed: {e}")

    @classmethod
    def reset_keep_logs(cls):
        """إعادة تعيين التقدم مع الاحتفاظ بالـ Logs"""
        try:
            data = cls.get()
            current_logs = data.get('logs')
            cls.reset()
            if current_logs:
                cls.update(logs=current_logs)
            print("✅ ProgressService: Reset with logs preserved")
        except Exception as e:
            print(f"❌ ProgressService.reset_keep_logs: Failed: {e}")