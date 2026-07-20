# imports/services/external_approval_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from pricing_requests.models import ExternalApproval
from imports.utils.import_helpers import ImportHelpers


class ExternalApprovalImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):
        """
        استيراد البيانات من شيت 12 - متابعة موافقات الخارجي
        """

        start_time = time.perf_counter()
        print("⏳ Starting External Approvals import from Sheet 12...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        # ============================================================
        # ✅ تخطي صف العناوين فقط
        # ============================================================
        data = dataframe.iloc[1:].copy()
        data = data.reset_index(drop=True)

        print(f"📊 عدد الصفوف بعد تخطي العناوين: {len(data)}")
        print("=" * 60)

        # ============================================================
        # ✅ Cache للـ External Approvals
        # ============================================================
        print("⏳ Loading existing external approvals...")
        approvals_cache = {}
        for approval in ExternalApproval.objects.all():
            # مفتاح البحث: الرقم الطبي + اسم المريض + التاريخ
            key = (
                ImportHelpers.normalize_text(approval.medical_number or ""),
                ImportHelpers.normalize_text(approval.patient_name or ""),
                approval.date,
            )
            approvals_cache[key] = approval
        print(f"   ✅ {len(approvals_cache)} approvals loaded")
        print("")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        to_create = []
        to_update = []

        # ============================================================
        # ✅ Loop
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(data)
        processed = 0

        for idx, row in data.iterrows():
            try:
                # ✅ قراءة البيانات
                patient_name = ImportHelpers.normalize_text(
                    row.iloc[2] if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                )

                # ✅ إذا كان اسم المريض فارغاً، نتخطى
                if not patient_name:
                    result["skipped"] += 1
                    continue

                # ✅ قراءة باقي البيانات
                attachment_type = ImportHelpers.normalize_text(
                    row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                )

                card_number = ImportHelpers.normalize_text(
                    row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                )

                company = ImportHelpers.normalize_text(
                    row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                )

                sub_account = ImportHelpers.normalize_text(
                    row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                )

                date = ImportHelpers.clean_date(
                    row.iloc[6] if len(row) > 6 and pd.notna(row.iloc[6]) else None
                )

                medical_number = ImportHelpers.normalize_text(
                    row.iloc[7] if len(row) > 7 and pd.notna(row.iloc[7]) else ""
                )

                doctor_name = ImportHelpers.normalize_text(
                    row.iloc[8] if len(row) > 8 and pd.notna(row.iloc[8]) else ""
                )

                specialty = ImportHelpers.normalize_text(
                    row.iloc[9] if len(row) > 9 and pd.notna(row.iloc[9]) else ""
                )

                required = ImportHelpers.normalize_text(
                    row.iloc[10] if len(row) > 10 and pd.notna(row.iloc[10]) else ""
                )

                procedure = ImportHelpers.normalize_text(
                    row.iloc[11] if len(row) > 11 and pd.notna(row.iloc[11]) else ""
                )

                phone = ImportHelpers.normalize_text(
                    row.iloc[12] if len(row) > 12 and pd.notna(row.iloc[12]) else ""
                )

                agent_1 = ImportHelpers.normalize_text(
                    row.iloc[13] if len(row) > 13 and pd.notna(row.iloc[13]) else ""
                )

                status = ImportHelpers.normalize_text(
                    row.iloc[14] if len(row) > 14 and pd.notna(row.iloc[14]) else ""
                )

                main_status = ImportHelpers.normalize_text(
                    row.iloc[15] if len(row) > 15 and pd.notna(row.iloc[15]) else ""
                )

                # ✅ الأرقام (Decimal)
                initial_cost = ImportHelpers.clean_decimal(
                    row.iloc[16] if len(row) > 16 and pd.notna(row.iloc[16]) else None
                )
                if initial_cost is None:
                    initial_cost = Decimal('0.00')

                pricing_date = ImportHelpers.clean_date(
                    row.iloc[17] if len(row) > 17 and pd.notna(row.iloc[17]) else None
                )

                pricing_responsible = ImportHelpers.normalize_text(
                    row.iloc[18] if len(row) > 18 and pd.notna(row.iloc[18]) else ""
                )

                billing_status = ImportHelpers.normalize_text(
                    row.iloc[19] if len(row) > 19 and pd.notna(row.iloc[19]) else ""
                )

                approval_review_responsible = ImportHelpers.normalize_text(
                    row.iloc[20] if len(row) > 20 and pd.notna(row.iloc[20]) else ""
                )

                accounts_notes = ImportHelpers.normalize_text(
                    row.iloc[21] if len(row) > 21 and pd.notna(row.iloc[21]) else ""
                )

                account_number = ImportHelpers.normalize_text(
                    row.iloc[22] if len(row) > 22 and pd.notna(row.iloc[22]) else ""
                )

                received_cost = ImportHelpers.clean_decimal(
                    row.iloc[23] if len(row) > 23 and pd.notna(row.iloc[23]) else None
                )
                if received_cost is None:
                    received_cost = Decimal('0.00')

                report = ImportHelpers.normalize_text(
                    row.iloc[24] if len(row) > 24 and pd.notna(row.iloc[24]) else ""
                )

                approval = ImportHelpers.normalize_text(
                    row.iloc[25] if len(row) > 25 and pd.notna(row.iloc[25]) else ""
                )

                request_approval_no = ImportHelpers.normalize_text(
                    row.iloc[26] if len(row) > 26 and pd.notna(row.iloc[26]) else ""
                )

                approval_date = ImportHelpers.clean_date(
                    row.iloc[27] if len(row) > 27 and pd.notna(row.iloc[27]) else None
                )

                expiry_date = ImportHelpers.clean_date(
                    row.iloc[28] if len(row) > 28 and pd.notna(row.iloc[28]) else None
                )

                notes = ImportHelpers.normalize_text(
                    row.iloc[29] if len(row) > 29 and pd.notna(row.iloc[29]) else ""
                )

                last_update = ImportHelpers.clean_date(
                    row.iloc[30] if len(row) > 30 and pd.notna(row.iloc[30]) else None
                )

                agent_2 = ImportHelpers.normalize_text(
                    row.iloc[31] if len(row) > 31 and pd.notna(row.iloc[31]) else ""
                )

                opd_sales_cs = ImportHelpers.normalize_text(
                    row.iloc[32] if len(row) > 32 and pd.notna(row.iloc[32]) else ""
                )

                admission_date = ImportHelpers.clean_date(
                    row.iloc[33] if len(row) > 33 and pd.notna(row.iloc[33]) else None
                )

                or_coordinator_notes = ImportHelpers.normalize_text(
                    row.iloc[34] if len(row) > 34 and pd.notna(row.iloc[34]) else ""
                )

                sales_account = ImportHelpers.normalize_text(
                    row.iloc[35] if len(row) > 35 and pd.notna(row.iloc[35]) else ""
                )

                head = ImportHelpers.normalize_text(
                    row.iloc[36] if len(row) > 36 and pd.notna(row.iloc[36]) else ""
                )

                user = ImportHelpers.normalize_text(
                    row.iloc[37] if len(row) > 37 and pd.notna(row.iloc[37]) else ""
                )

                sales_notes = ImportHelpers.normalize_text(
                    row.iloc[38] if len(row) > 38 and pd.notna(row.iloc[38]) else ""
                )

                result["processed"] += 1
                processed = result["processed"]

                # ✅ البحث في Cache
                key = (
                    medical_number,
                    patient_name,
                    date,
                )
                existing_approval = approvals_cache.get(key)

                if existing_approval:
                    # ✅ تحديث البيانات
                    changed = False
                    
                    # قائمة الحقول للتحديث
                    fields_to_check = [
                        ("attachment_type", attachment_type),
                        ("card_number", card_number),
                        ("company", company),
                        ("sub_account", sub_account),
                        ("doctor_name", doctor_name),
                        ("specialty", specialty),
                        ("required", required),
                        ("procedure", procedure),
                        ("phone", phone),
                        ("agent_1", agent_1),
                        ("status", status),
                        ("main_status", main_status),
                        ("initial_cost", initial_cost),
                        ("pricing_responsible", pricing_responsible),
                        ("billing_status", billing_status),
                        ("approval_review_responsible", approval_review_responsible),
                        ("accounts_notes", accounts_notes),
                        ("account_number", account_number),
                        ("received_cost", received_cost),
                        ("report", report),
                        ("approval", approval),
                        ("request_approval_no", request_approval_no),
                        ("approval_date", approval_date),
                        ("expiry_date", expiry_date),
                        ("notes", notes),
                        ("last_update", last_update),
                        ("agent_2", agent_2),
                        ("opd_sales_cs", opd_sales_cs),
                        ("admission_date", admission_date),
                        ("or_coordinator_notes", or_coordinator_notes),
                        ("sales_account", sales_account),
                        ("head", head),
                        ("user", user),
                        ("sales_notes", sales_notes),
                    ]
                    
                    for field_name, value in fields_to_check:
                        if getattr(existing_approval, field_name) != value:
                            setattr(existing_approval, field_name, value)
                            changed = True
                    
                    if changed:
                        to_update.append(existing_approval)
                        result["updated"] += 1

                else:
                    # ✅ إنشاء جديد
                    approval = ExternalApproval(
                        attachment_type=attachment_type,
                        patient_name=patient_name,
                        card_number=card_number,
                        company=company,
                        sub_account=sub_account,
                        date=date,
                        medical_number=medical_number,
                        doctor_name=doctor_name,
                        specialty=specialty,
                        required=required,
                        procedure=procedure,
                        phone=phone,
                        agent_1=agent_1,
                        status=status,
                        main_status=main_status,
                        initial_cost=initial_cost,
                        pricing_date=pricing_date,
                        pricing_responsible=pricing_responsible,
                        billing_status=billing_status,
                        approval_review_responsible=approval_review_responsible,
                        accounts_notes=accounts_notes,
                        account_number=account_number,
                        received_cost=received_cost,
                        report=report,
                        approval=approval,
                        request_approval_no=request_approval_no,
                        approval_date=approval_date,
                        expiry_date=expiry_date,
                        notes=notes,
                        last_update=last_update,
                        agent_2=agent_2,
                        opd_sales_cs=opd_sales_cs,
                        admission_date=admission_date,
                        or_coordinator_notes=or_coordinator_notes,
                        sales_account=sales_account,
                        head=head,
                        user=user,
                        sales_notes=sales_notes,
                    )
                    to_create.append(approval)
                    approvals_cache[key] = approval
                    result["created"] += 1

                # عرض التقدم
                if processed % 100 == 0:
                    print(f"   📊 Processed {processed}/{total_rows} rows...")

            except Exception as e:
                result["errors"] += 1
                if result["errors"] <= 10:
                    patient_name = row.iloc[2] if len(row) > 2 and pd.notna(row.iloc[2]) else "غير معروف"
                    print(f"\n❌ خطأ في الصف {idx + 2}: {str(e)[:80]}...")
                    print(f"   Patient: {patient_name}")
                continue

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} approvals...")
        print(f"💾 Updating {len(to_update)} approvals...")

        if to_create:
            ExternalApproval.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            ExternalApproval.objects.bulk_update(
                to_update,
                fields=[
                    "attachment_type", "card_number", "company", "sub_account",
                    "doctor_name", "specialty", "required", "procedure", "phone",
                    "agent_1", "status", "main_status", "initial_cost",
                    "pricing_responsible", "billing_status", "approval_review_responsible",
                    "accounts_notes", "account_number", "received_cost", "report",
                    "approval", "request_approval_no", "approval_date", "expiry_date",
                    "notes", "last_update", "agent_2", "opd_sales_cs", "admission_date",
                    "or_coordinator_notes", "sales_account", "head", "user", "sales_notes",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time

        # عرض النتائج النهائية
        print("\n" + "=" * 60)
        print("✅ انتهى الاستيراد")
        print(f"📊 Processed : {result['processed']}")
        print(f"✅ Created   : {result['created']}")
        print(f"🔄 Updated   : {result['updated']}")
        print(f"⏭️ Skipped   : {result['skipped']}")
        if result["errors"] > 0:
            print(f"❌ Errors    : {result['errors']}")
        print(f"⏱️ الوقت     : {elapsed:.2f} ثانية")
        print("=" * 60)

        return result