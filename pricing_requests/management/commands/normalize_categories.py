# pricing_requests/management/commands/normalize_categories.py

from django.core.management.base import BaseCommand
from pricing_requests.models import ProcedureFee


class Command(BaseCommand):
    help = 'توحيد التصنيفات في جدول ProcedureFee لتطابق جدول Procedure'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("🔄 بدء توحيد التصنيفات...")
        self.stdout.write("=" * 60)
        
        mapping = {
            'صغرى': 'صغـــرى',
            'كبرى': 'كــبرى',
            'طابع خاص': 'ذات طابع خاص',
            'صغرى ': 'صغـــرى',
            'كبرى ': 'كــبرى',
            'طابع خاص ': 'ذات طابع خاص',
        }
        
        total_updated = 0
        
        for old, new in mapping.items():
            count = ProcedureFee.objects.filter(category=old).update(category=new)
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ تم تحديث {count} سجل من '{old}' إلى '{new}'")
                )
                total_updated += count
        
        self.stdout.write("=" * 60)
        if total_updated == 0:
            self.stdout.write(self.style.WARNING("⚠️ لا توجد تصنيفات تحتاج إلى تحديث"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ تم توحيد {total_updated} سجل بنجاح!")
            )
        self.stdout.write("=" * 60)