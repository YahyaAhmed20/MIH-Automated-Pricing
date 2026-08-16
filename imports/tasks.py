from io import StringIO
import time
from celery import shared_task
from django.core.cache import cache

from imports.services.progress_service import ProgressService
from imports.services.update_all_data_service import (
    UpdateAllDataService,
    IMPORT_COMMANDS,
    POST_IMPORT_COMMANDS,
)
from imports.exceptions import TaskCancelled


@shared_task(bind=True)
def update_all_data_task(self):
    
    output = StringIO()
    
    total = len(IMPORT_COMMANDS) + len(POST_IMPORT_COMMANDS)
    
    # ✅ إعادة تعيين التقدم
    ProgressService.reset()
    
    # ✅ ضبط الحالة الأولية
    ProgressService.update(
        status="running",
        is_running=True,
        total=total,
        logs=None,
        completed=0,
        current_command="⏳ جاري التهيئة...",
    )
    
    try:
        
        def progress_callback(command_name, completed):
            # ✅ التحقق من طلب الإلغاء
            if ProgressService.is_cancel_requested():
                raise TaskCancelled()
            
            # ✅ تأخير بسيط لتقليل الضغط على Redis
            time.sleep(0.05)
            
            # ✅ تحديث التقدم
            ProgressService.update(
                current_command=command_name,
                completed=completed,
            )
        
        # ✅ تشغيل التحديث
        UpdateAllDataService.run(
            stdout=output,
            progress_callback=progress_callback,
        )
        
        logs = output.getvalue()
        
        # ✅ مسح الـ Cache
        try:
            cache.clear()
            logs += "\n\n✅ تم مسح الـ Cache بنجاح"
        except Exception as e:
            logs += f"\n\n⚠️ فشل مسح الـ Cache: {str(e)}"
        
        # ✅ تحديث الحالة النهائية
        ProgressService.update(
            status="completed",
            is_running=False,
            completed=total,
            total=total,
            logs=logs,
            current_command="✅ تم الانتهاء من جميع الأوامر بنجاح!",
        )
        
        return {
            "status": "success",
            "logs": logs,
        }
        
    except TaskCancelled:
        
        logs = output.getvalue()
        
        # ✅ تحديث حالة الإلغاء
        ProgressService.update(
            status="cancelled",
            is_running=False,
            completed=ProgressService.get().get("completed", 0),
            logs=logs + "\n\n🛑 تم إلغاء العملية بواسطة المستخدم.",
            current_command="🛑 تم الإلغاء",
        )
        
        return {
            "status": "cancelled",
        }
        
    except Exception as exc:
        
        error_logs = output.getvalue()
        
        # ✅ تحديث حالة الخطأ
        ProgressService.update(
            status="error",
            is_running=False,
            logs=error_logs + f"\n\n❌ خطأ: {exc}",
            current_command=f"❌ خطأ: {str(exc)[:50]}...",
        )
        
        raise