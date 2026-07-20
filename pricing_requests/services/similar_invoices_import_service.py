# pricing_requests/services/similar_invoices_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from pricing_requests.models import SimilarInvoice
from imports.utils.import_helpers import ImportHelpers


class SimilarInvoicesImportService:

    @staticmethod
    def truncate_text(value, max_length=255):
        """تقليص النص إذا تجاوز الحد الأقصى"""
        if not value:
            return value
        # إزالة الأحرف الخاصة والمسافات الزائدة أولاً
        cleaned = ImportHelpers.normalize_text(value)
        if len(cleaned) > max_length:
            print(f"⚠️ تم تقليص نص طويل من {len(cleaned)} إلى {max_length} حرف")
            return cleaned[:max_length]
        return cleaned

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Similar Invoices import from Sheet 10...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Similar Invoices
        # ============================================================
        print("⏳ Loading existing similar invoices...")
        records_cache = {}
        
        for record in SimilarInvoice.objects.all():
            key = (
                ImportHelpers.normalize_text(record.account_number or ""),
                ImportHelpers.normalize_text(record.operation_name or ""),
                ImportHelpers.normalize_text(record.patient_name or ""),
                record.admission_date,
            )
            records_cache[key] = record
            
        print(f"   ✅ {len(records_cache)} records loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        to_create = []
        to_update = []

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ أرقام الأعمدة حسب ترتيب شيت 10
            # العمود 0: الرقم الحسابي
            account_number = ImportHelpers.normalize_text(row.get(0, ""))
            
            # العمود 1: الرقم الطبي
            medical_number = ImportHelpers.normalize_text(row.get(1, ""))
            
            # العمود 2: اسم المريض
            patient_name = ImportHelpers.normalize_text(row.get(2, ""))
            
            # العمود 3: تاريخ الدخول
            admission_date = ImportHelpers.clean_date(row.get(3, None))
            
            # العمود 4: تاريخ الخروج
            discharge_date = ImportHelpers.clean_date(row.get(4, None))
            
            # العمود 5: مدة الاقامه
            stay_duration_raw = ImportHelpers.clean_decimal(row.get(5, None))
            if stay_duration_raw is not None:
                stay_duration = str(int(stay_duration_raw))
            else:
                stay_duration = ""
            
            # العمود 6: التخصص
            specialty_name = ImportHelpers.normalize_text(row.get(6, ""))
            
            # العمود 7: اسم الطبيب
            doctor_name = ImportHelpers.normalize_text(row.get(7, ""))
            
            # العمود 8: اسم العمليه - ✅ تطبيق التقليص
            operation_name = ImportHelpers.normalize_text(row.get(8, ""))
            operation_name = SimilarInvoicesImportService.truncate_text(operation_name, 255)
            
            # العمود 9: الجهه - ✅ تطبيق التقليص
            entity_name = ImportHelpers.normalize_text(row.get(9, ""))
            entity_name = SimilarInvoicesImportService.truncate_text(entity_name, 255)
            
            # العمود 10: الشركة الفرعية - ✅ تطبيق التقليص
            sub_company = ImportHelpers.normalize_text(row.get(10, ""))
            sub_company = SimilarInvoicesImportService.truncate_text(sub_company, 255)
            
            # العمود 11: الدور / المبني - ✅ تطبيق التقليص
            building = ImportHelpers.normalize_text(row.get(11, ""))
            building = SimilarInvoicesImportService.truncate_text(building, 255)
            
            # العمود 12: اجمالي الفاتوره
            total_invoice = ImportHelpers.clean_decimal(row.get(12, None))
            if total_invoice is None:
                total_invoice = Decimal('0.00')
            
            # العمود 13: الخصم
            discount = ImportHelpers.clean_decimal(row.get(13, None))
            if discount is None:
                discount = Decimal('0.00')
            
            # العمود 14: صافي الفاتوره
            net_invoice = ImportHelpers.clean_decimal(row.get(14, None))
            if net_invoice is None:
                net_invoice = Decimal('0.00')
            
            # العمود 15: حصة الشركه
            company_share = ImportHelpers.clean_decimal(row.get(15, None))
            if company_share is None:
                company_share = Decimal('0.00')
            
            # العمود 16: حصة المريض
            patient_share = ImportHelpers.clean_decimal(row.get(16, None))
            if patient_share is None:
                patient_share = Decimal('0.00')
            
            # العمود 17: المدفوعات
            payments = ImportHelpers.clean_decimal(row.get(17, None))
            if payments is None:
                payments = Decimal('0.00')
            
            # العمود 18: حالة الفاتورة - ✅ تطبيق التقليص
            invoice_status = ImportHelpers.normalize_text(row.get(18, ""))
            invoice_status = SimilarInvoicesImportService.truncate_text(invoice_status, 255)
            
            # العمود 19: تاريخ انهاء الفاتوره
            invoice_closed_date = ImportHelpers.clean_date(row.get(19, None))
            
            # العمود 20: ملاحظات - ✅ تطبيق التقليص
            notes = ImportHelpers.normalize_text(row.get(20, ""))
            notes = SimilarInvoicesImportService.truncate_text(notes, 255)

            # ✅ قيم افتراضية
            if not account_number:
                account_number = f"UNKNOWN_ACCOUNT_{index}"
                print(f"⚠️ صف {index}: الرقم الحسابي مفقود - تم استخدام رقم افتراضي")

            if not patient_name:
                patient_name = f"UNKNOWN_PATIENT_{index}"
                print(f"⚠️ صف {index}: اسم المريض مفقود - تم استخدام اسم افتراضي")

            if not operation_name:
                operation_name = f"UNKNOWN_OPERATION_{index}"
                print(f"⚠️ صف {index}: اسم العملية مفقود - تم استخدام اسم افتراضي")

            # ✅ تخطي الصفوف التي لا تحتوي على بيانات مفيدة
            if not account_number and not patient_name and not operation_name:
                result["skipped"] += 1
                continue

            result["processed"] += 1
            processed = result["processed"]

            # ✅ البحث في Cache
            key = (
                account_number,
                operation_name,
                patient_name,
                admission_date,
            )
            
            existing_record = records_cache.get(key)

            if existing_record:
                # ✅ تحديث البيانات
                changed = False
                
                if existing_record.medical_number != medical_number:
                    existing_record.medical_number = medical_number
                    changed = True
                    
                if existing_record.discharge_date != discharge_date:
                    existing_record.discharge_date = discharge_date
                    changed = True
                    
                if existing_record.stay_duration != stay_duration:
                    existing_record.stay_duration = stay_duration
                    changed = True
                    
                if existing_record.specialty_name != specialty_name:
                    existing_record.specialty_name = specialty_name
                    changed = True
                    
                if existing_record.doctor_name != doctor_name:
                    existing_record.doctor_name = doctor_name
                    changed = True
                    
                if existing_record.entity_name != entity_name:
                    existing_record.entity_name = entity_name
                    changed = True
                    
                if existing_record.sub_company != sub_company:
                    existing_record.sub_company = sub_company
                    changed = True
                    
                if existing_record.building != building:
                    existing_record.building = building
                    changed = True
                    
                if existing_record.total_invoice != total_invoice:
                    existing_record.total_invoice = total_invoice
                    changed = True
                    
                if existing_record.discount != discount:
                    existing_record.discount = discount
                    changed = True
                    
                if existing_record.net_invoice != net_invoice:
                    existing_record.net_invoice = net_invoice
                    changed = True
                    
                if existing_record.company_share != company_share:
                    existing_record.company_share = company_share
                    changed = True
                    
                if existing_record.patient_share != patient_share:
                    existing_record.patient_share = patient_share
                    changed = True
                    
                if existing_record.payments != payments:
                    existing_record.payments = payments
                    changed = True
                    
                if existing_record.invoice_status != invoice_status:
                    existing_record.invoice_status = invoice_status
                    changed = True
                    
                if existing_record.invoice_closed_date != invoice_closed_date:
                    existing_record.invoice_closed_date = invoice_closed_date
                    changed = True
                    
                if existing_record.notes != notes:
                    existing_record.notes = notes
                    changed = True

                if changed:
                    to_update.append(existing_record)
                    result["updated"] += 1

            else:
                # ✅ إنشاء جديد
                record = SimilarInvoice(
                    account_number=account_number,
                    medical_number=medical_number,
                    patient_name=patient_name,
                    admission_date=admission_date,
                    discharge_date=discharge_date,
                    stay_duration=stay_duration,
                    specialty_name=specialty_name,
                    doctor_name=doctor_name,
                    operation_name=operation_name,
                    entity_name=entity_name,
                    sub_company=sub_company,
                    building=building,
                    total_invoice=total_invoice,
                    discount=discount,
                    net_invoice=net_invoice,
                    company_share=company_share,
                    patient_share=patient_share,
                    payments=payments,
                    invoice_status=invoice_status,
                    invoice_closed_date=invoice_closed_date,
                    notes=notes,
                )
                to_create.append(record)
                records_cache[key] = record
                result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} records...")
        print(f"💾 Updating {len(to_update)} records...")

        if to_create:
            SimilarInvoice.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            SimilarInvoice.objects.bulk_update(
                to_update,
                fields=[
                    "medical_number",
                    "discharge_date",
                    "stay_duration",
                    "specialty_name",
                    "doctor_name",
                    "entity_name",
                    "sub_company",
                    "building",
                    "total_invoice",
                    "discount",
                    "net_invoice",
                    "company_share",
                    "patient_share",
                    "payments",
                    "invoice_status",
                    "invoice_closed_date",
                    "notes",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result