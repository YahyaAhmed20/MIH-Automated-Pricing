# imports/services/report_statistic_import_service.py

from django.db import transaction
import pandas as pd

from pricing_requests.models import ReportStatistic
from imports.utils.import_helpers import ImportHelpers


class ReportStatisticImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):
        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }
        
        # ✅ تخطي الصف الأول (العناوين)
        data = dataframe.iloc[1:].copy()
        data = data.reset_index(drop=True)
        
        print(f"📊 عدد الصفوف بعد تخطي العناوين: {len(data)}")
        print("=" * 50)
        
        for idx, row in data.iterrows():
            try:
                # ✅ قراءة البيانات
                patient_name = ""
                if len(row) > 2 and pd.notna(row.iloc[2]):
                    patient_name = ImportHelpers.normalize_text(row.iloc[2])
                
                if not patient_name:
                    result["skipped"] += 1
                    continue
                
                # ✅ قراءة باقي البيانات
                medical_number = ""
                if len(row) > 0 and pd.notna(row.iloc[0]):
                    medical_number = ImportHelpers.normalize_text(row.iloc[0])
                
                account_number = ""
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    account_number = ImportHelpers.normalize_text(row.iloc[1])
                
                # ✅ التواريخ
                admission_date = None
                if len(row) > 3 and pd.notna(row.iloc[3]):
                    admission_date = ImportHelpers.clean_date(row.iloc[3])
                
                discharge_date = None
                if len(row) > 4 and pd.notna(row.iloc[4]):
                    discharge_date = ImportHelpers.clean_date(row.iloc[4])
                
                month = ""
                if len(row) > 5 and pd.notna(row.iloc[5]):
                    month = ImportHelpers.normalize_text(row.iloc[5])
                
                specialty = ""
                if len(row) > 6 and pd.notna(row.iloc[6]):
                    specialty = ImportHelpers.normalize_text(row.iloc[6])
                
                package_name = ""
                if len(row) > 7 and pd.notna(row.iloc[7]):
                    package_name = ImportHelpers.normalize_text(row.iloc[7])
                
                entity_name = ""
                if len(row) > 8 and pd.notna(row.iloc[8]):
                    entity_name = ImportHelpers.normalize_text(row.iloc[8])
                
                sector = ""
                if len(row) > 9 and pd.notna(row.iloc[9]):
                    sector = ImportHelpers.normalize_text(row.iloc[9])
                
                payment_type = ""
                if len(row) > 10 and pd.notna(row.iloc[10]):
                    payment_type = ImportHelpers.normalize_text(row.iloc[10])
                
                sub_company = ""
                if len(row) > 11 and pd.notna(row.iloc[11]):
                    sub_company = ImportHelpers.normalize_text(row.iloc[11])
                
                # ✅ المبلغ
                amount = 0
                if len(row) > 12 and pd.notna(row.iloc[12]):
                    amount_raw = row.iloc[12]
                    if isinstance(amount_raw, (int, float)):
                        amount = float(amount_raw)
                    else:
                        try:
                            amount = float(str(amount_raw).replace(",", ""))
                        except:
                            amount = 0
                
                # ✅ ✅ ✅ استخدم create بدون أي تتبع للتكرار
                # ✅ كل سجل في الـ Excel يتحول إلى سجل في قاعدة البيانات
                obj = ReportStatistic.objects.create(
                    medical_number=medical_number,
                    account_number=account_number,
                    patient_name=patient_name,
                    admission_date=admission_date,
                    discharge_date=discharge_date,
                    month=month,
                    specialty=specialty,
                    package_name=package_name,
                    entity_name=entity_name,
                    sector=sector,
                    payment_type=payment_type,
                    sub_company=sub_company,
                    amount=amount,
                )
                
                result["processed"] += 1
                result["created"] += 1
                
                # ✅ عرض التقدم كل 100 سجل
                if result["processed"] % 100 == 0:
                    print(f"   📊 تم معالجة {result['processed']} سجل...")
                    
            except Exception as e:
                result["errors"] += 1
                if result["errors"] <= 10:
                    print(f"   ❌ خطأ في الصف {idx + 2}: {str(e)[:80]}...")
                continue
        
        # ✅ عرض النتائج النهائية
        print("\n" + "=" * 50)
        print("✅ انتهى الاستيراد!")
        print(f"   📊 تمت المعالجة: {result['processed']}")
        print(f"   ✅ تم الإنشاء: {result['created']}")
        print(f"   🔄 تم التحديث: {result['updated']}")
        print(f"   ⏭️ تم التخطي: {result['skipped']}")
        if result["errors"] > 0:
            print(f"   ❌ الأخطاء: {result['errors']}")
        print("=" * 50)
        
        return result