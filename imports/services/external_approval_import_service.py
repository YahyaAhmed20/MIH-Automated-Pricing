# imports/services/external_approval_import_service.py

from django.db import transaction
import pandas as pd

from pricing_requests.models import ExternalApproval
from imports.utils.import_helpers import ImportHelpers


class ExternalApprovalImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):
        """
        استيراد البيانات من شيت 12 - متابعة موافقات الخارجي
        """
        
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
                patient_name = ImportHelpers.normalize_text(
                    row.iloc[2] if len(row) > 2 and pd.notna(row.iloc[2]) else None
                )
                
                if not patient_name:
                    result["skipped"] += 1
                    continue
                
                # ✅ ✅ ✅ استخدم create بدل update_or_create
                # ✅ كل سجل في الـ Excel يتحول إلى سجل في قاعدة البيانات
                obj = ExternalApproval.objects.create(
                    attachment_type=ImportHelpers.normalize_text(
                        row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None
                    ),
                    patient_name=patient_name,
                    card_number=ImportHelpers.normalize_text(
                        row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else None
                    ),
                    company=ImportHelpers.normalize_text(
                        row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else None
                    ),
                    sub_account=ImportHelpers.normalize_text(
                        row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else None
                    ),
                    date=ImportHelpers.clean_date(
                        row.iloc[6] if len(row) > 6 and pd.notna(row.iloc[6]) else None
                    ),
                    medical_number=ImportHelpers.normalize_text(
                        row.iloc[7] if len(row) > 7 and pd.notna(row.iloc[7]) else None
                    ),
                    doctor_name=ImportHelpers.normalize_text(
                        row.iloc[8] if len(row) > 8 and pd.notna(row.iloc[8]) else None
                    ),
                    specialty=ImportHelpers.normalize_text(
                        row.iloc[9] if len(row) > 9 and pd.notna(row.iloc[9]) else None
                    ),
                    required=ImportHelpers.normalize_text(
                        row.iloc[10] if len(row) > 10 and pd.notna(row.iloc[10]) else None
                    ),
                    procedure=ImportHelpers.normalize_text(
                        row.iloc[11] if len(row) > 11 and pd.notna(row.iloc[11]) else None
                    ),
                    phone=ImportHelpers.normalize_text(
                        row.iloc[12] if len(row) > 12 and pd.notna(row.iloc[12]) else None
                    ),
                    agent_1=ImportHelpers.normalize_text(
                        row.iloc[13] if len(row) > 13 and pd.notna(row.iloc[13]) else None
                    ),
                    status=ImportHelpers.normalize_text(
                        row.iloc[14] if len(row) > 14 and pd.notna(row.iloc[14]) else None
                    ),
                    main_status=ImportHelpers.normalize_text(
                        row.iloc[15] if len(row) > 15 and pd.notna(row.iloc[15]) else None
                    ),
                    initial_cost=ImportHelpers.clean_decimal(
                        row.iloc[16] if len(row) > 16 and pd.notna(row.iloc[16]) else None
                    ) or 0,
                    pricing_date=ImportHelpers.clean_date(
                        row.iloc[17] if len(row) > 17 and pd.notna(row.iloc[17]) else None
                    ),
                    pricing_responsible=ImportHelpers.normalize_text(
                        row.iloc[18] if len(row) > 18 and pd.notna(row.iloc[18]) else None
                    ),
                    billing_status=ImportHelpers.normalize_text(
                        row.iloc[19] if len(row) > 19 and pd.notna(row.iloc[19]) else None
                    ),
                    approval_review_responsible=ImportHelpers.normalize_text(
                        row.iloc[20] if len(row) > 20 and pd.notna(row.iloc[20]) else None
                    ),
                    accounts_notes=ImportHelpers.normalize_text(
                        row.iloc[21] if len(row) > 21 and pd.notna(row.iloc[21]) else None
                    ),
                    account_number=ImportHelpers.normalize_text(
                        row.iloc[22] if len(row) > 22 and pd.notna(row.iloc[22]) else None
                    ),
                    received_cost=ImportHelpers.clean_decimal(
                        row.iloc[23] if len(row) > 23 and pd.notna(row.iloc[23]) else None
                    ) or 0,
                    report=ImportHelpers.normalize_text(
                        row.iloc[24] if len(row) > 24 and pd.notna(row.iloc[24]) else None
                    ),
                    approval=ImportHelpers.normalize_text(
                        row.iloc[25] if len(row) > 25 and pd.notna(row.iloc[25]) else None
                    ),
                    request_approval_no=ImportHelpers.normalize_text(
                        row.iloc[26] if len(row) > 26 and pd.notna(row.iloc[26]) else None
                    ),
                    approval_date=ImportHelpers.clean_date(
                        row.iloc[27] if len(row) > 27 and pd.notna(row.iloc[27]) else None
                    ),
                    expiry_date=ImportHelpers.clean_date(
                        row.iloc[28] if len(row) > 28 and pd.notna(row.iloc[28]) else None
                    ),
                    notes=ImportHelpers.normalize_text(
                        row.iloc[29] if len(row) > 29 and pd.notna(row.iloc[29]) else None
                    ),
                    last_update=ImportHelpers.clean_date(
                        row.iloc[30] if len(row) > 30 and pd.notna(row.iloc[30]) else None
                    ),
                    agent_2=ImportHelpers.normalize_text(
                        row.iloc[31] if len(row) > 31 and pd.notna(row.iloc[31]) else None
                    ),
                    opd_sales_cs=ImportHelpers.normalize_text(
                        row.iloc[32] if len(row) > 32 and pd.notna(row.iloc[32]) else None
                    ),
                    admission_date=ImportHelpers.clean_date(
                        row.iloc[33] if len(row) > 33 and pd.notna(row.iloc[33]) else None
                    ),
                    or_coordinator_notes=ImportHelpers.normalize_text(
                        row.iloc[34] if len(row) > 34 and pd.notna(row.iloc[34]) else None
                    ),
                    sales_account=ImportHelpers.normalize_text(
                        row.iloc[35] if len(row) > 35 and pd.notna(row.iloc[35]) else None
                    ),
                    head=ImportHelpers.normalize_text(
                        row.iloc[36] if len(row) > 36 and pd.notna(row.iloc[36]) else None
                    ),
                    user=ImportHelpers.normalize_text(
                        row.iloc[37] if len(row) > 37 and pd.notna(row.iloc[37]) else None
                    ),
                    sales_notes=ImportHelpers.normalize_text(
                        row.iloc[38] if len(row) > 38 and pd.notna(row.iloc[38]) else None
                    ),
                )
                
                result["processed"] += 1
                result["created"] += 1
                
                if result["processed"] % 50 == 0:
                    print(f"   📊 تم معالجة {result['processed']} سجل...")
                    
            except Exception as e:
                result["errors"] += 1
                if result["errors"] <= 10:
                    print(f"   ❌ خطأ في الصف {idx + 2}: {str(e)[:80]}...")
                continue
        
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