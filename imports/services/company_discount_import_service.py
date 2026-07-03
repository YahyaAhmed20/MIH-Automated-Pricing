from django.db import transaction

import pandas as pd

from contracts.models import (
    CompanyDiscountProfile,
    CompanyDiscount,
)

from imports.utils.import_helpers import (
    ImportHelpers,
)


class CompanyDiscountImportService:
    
    INTERNAL_ITEMS = [

        {
            "name": "البنود الخاضعه للخصم",
            "discount_col": 4,
            "details_col": None,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "الاقامه",
            "discount_col": 6,
            "details_col": 7,
            "net_price_col": 8,
            "is_percentage": True,
        },

        {
            "name": "المعمل",
            "discount_col": 9,
            "details_col": 10,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "الاشعه",
            "discount_col": 11,
            "details_col": 12,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "اتعاب الاطباء",
            "discount_col": 13,
            "details_col": 14,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "الاشراف الطبي",
            "discount_col": 19,
            "details_col": 20,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "فتح غرفة العمليات",
            "discount_col": 21,
            "details_col": 22,
            "net_price_col": 23,
            "is_percentage": True,
        },

        {
            "name": "اجهزة العمليات",
            "discount_col": 24,
            "details_col": 25,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "خدمات الرعاية المركزة",
            "discount_col": 26,
            "details_col": 27,
            "net_price_col": None,
            "is_percentage": True,
        },

    ]

    EXTERNAL_ITEMS = [

        {
            "name": "البنود الخاضعه للخصم",
            "discount_col": 30,
            "details_col": None,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "كشف العيادة الخارجية",
            "discount_col": 32,
            "details_col": 33,
            "net_price_col": None,
            "is_percentage": False,
        },

        {
            "name": "خدمات القسم الخارجي",
            "discount_col": 34,
            "details_col": 35,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "كشف الطوارئ",
            "discount_col": 36,
            "details_col": 37,
            "net_price_col": None,
            "is_percentage": False,
        },

        {
            "name": "خدمات الطوارئ",
            "discount_col": 38,
            "details_col": 39,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "المعمل",
            "discount_col": 40,
            "details_col": 41,
            "net_price_col": None,
            "is_percentage": True,
        },

        {
            "name": "الاشعه",
            "discount_col": 42,
            "details_col": 43,
            "net_price_col": None,
            "is_percentage": True,
        },

    ]

    # ============================================================
    # Import Data
    # ============================================================
    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created_profiles": 0,
            "updated_profiles": 0,
            "created_discounts": 0,
        }

        i = 2

        while i < len(dataframe):

            row = dataframe.iloc[i]

            company_name = ImportHelpers.normalize_text(
                row.get("الجهه")
            )

            financial_code = ImportHelpers.normalize_text(
                row.get("الفئه الماليه")
            )

            if not company_name:
                i += 7
                continue

            result["processed"] += 1

            contract_type = ImportHelpers.normalize_text(
                row.get("نوع التعاقد")
            )

            price_list = ImportHelpers.normalize_text(
                row.get("قائمة الاسعار")
            )

            operating_pdf = ImportHelpers.normalize_text(
                row.get("المرفقات")
            )

            profile, created = CompanyDiscountProfile.objects.update_or_create(

                company_name=company_name,

                financial_category=financial_code,

                defaults={

                    "contract_type": contract_type,

                    "price_list": price_list,

                    "operating_pdf": operating_pdf,

                    "is_active": True,

                }

            )

            if created:
                result["created_profiles"] += 1
            else:
                result["updated_profiles"] += 1

            # ✅ حذف خصومات الـ Profile الحالي فقط
            CompanyDiscount.objects.filter(
                profile=profile
            ).delete()

            # ==========================================
            # القسم الداخلي
            # ==========================================

            order = 1

            for item in CompanyDiscountImportService.INTERNAL_ITEMS:

                raw_discount = row.iloc[item["discount_col"]]

                if item["is_percentage"]:
                    discount = ImportHelpers.clean_discount(
                        raw_discount
                    )
                else:
                    discount = ImportHelpers.normalize_text(
                        raw_discount
                    )

                details = ""

                # ==========================================
                # الإقامة
                # ==========================================

                if item["name"] == "الاقامه":

                    lines = []

                    for offset in range(7):

                        current_row = dataframe.iloc[i + offset]

                        room_name = ImportHelpers.normalize_text(
                            current_row.iloc[7]
                        )

                        price = ImportHelpers.clean_decimal(
                            current_row.iloc[8]
                        )

                        room_price = (
                            f"{price:,.0f}"
                            if price is not None
                            else ""
                        )

                        if room_name:

                            lines.append(
                                f"{room_name} : {room_price}"
                            )

                    details = "\n".join(lines)

                # ==========================================
                # فتح غرفة العمليات
                # ==========================================

                elif item["name"] == "فتح غرفة العمليات":

                    lines = []

                    for offset in range(6):

                        current_row = dataframe.iloc[i + offset]

                        operation_type = ImportHelpers.normalize_text(
                            current_row.iloc[22]
                        )

                        price = ImportHelpers.clean_decimal(
                            current_row.iloc[23]
                        )

                        operation_price = (
                            f"{price:,.0f}"
                            if price is not None
                            else ""
                        )

                        if operation_type:

                            lines.append(
                                f"{operation_type} : {operation_price}"
                            )

                    details = "\n".join(lines)

                # ==========================================
                # اتعاب الاطباء
                # ==========================================

                elif item["name"] == "اتعاب الاطباء":

                    lines = []

                    for offset in range(6):

                        current_row = dataframe.iloc[i + offset]

                        level = ImportHelpers.normalize_text(
                            current_row.iloc[14]
                        )

                        if not level:
                            continue

                        surgeon = ImportHelpers.clean_decimal(
                            current_row.iloc[15]
                        )

                        anesthesia = ImportHelpers.clean_decimal(
                            current_row.iloc[16]
                        )

                        assistant = ImportHelpers.clean_decimal(
                            current_row.iloc[17]
                        )

                        total = ImportHelpers.clean_decimal(
                            current_row.iloc[18]
                        )

                        def fmt(value):
                            return f"{value:,.0f}" if value is not None else "-"

                        lines.append(
                            (
                                f"{level}\n"
                                f"جراح : {fmt(surgeon)}\n"
                                f"تخدير : {fmt(anesthesia)}\n"
                                f"مساعد : {fmt(assistant)}\n"
                                f"الإجمالي : {fmt(total)}"
                            )
                        )

                    details = "\n\n".join(lines)

                # ==========================================
                # باقي البنود
                # ==========================================

                elif item["details_col"] is not None:

                    raw_details = row.iloc[item["details_col"]]

                    if pd.notna(raw_details):

                        details = str(raw_details).strip()

                # ==========================================
                # net_price
                # ==========================================

                net_price = None

                # ✅ لو الإقامة أو فتح غرفة العمليات، نخلي net_price = None عشان منكرر السعر
                if item["name"] not in ["الاقامه", "فتح غرفة العمليات"]:
                    if item["net_price_col"] is not None:
                        net_price = ImportHelpers.clean_decimal(
                            row.iloc[item["net_price_col"]]
                        )

                CompanyDiscount.objects.create(

                    profile=profile,

                    section="داخلي",

                    item_name=item["name"],

                    discount=discount,

                    details=details,

                    net_price=net_price,

                    display_order=order,

                    is_active=True,

                )

                result["created_discounts"] += 1

                order += 1

            # ==========================================
            # الاستثناءات الداخلية
            # ==========================================

            internal_exception = ImportHelpers.normalize_text(
                row.iloc[28]
            )

            CompanyDiscount.objects.create(

                profile=profile,

                section="داخلي",

                item_name="الاستثناءات",

                details=internal_exception,

                display_order=100,

                is_active=True,

            )

            result["created_discounts"] += 1

            # ==========================================
            # القسم الخارجي
            # ==========================================

            order = 1

            for item in CompanyDiscountImportService.EXTERNAL_ITEMS:

                raw_discount = row.iloc[item["discount_col"]]

                if item["is_percentage"]:
                    discount = ImportHelpers.clean_discount(
                        raw_discount
                    )
                else:
                    discount = ImportHelpers.normalize_text(
                        raw_discount
                    )

                details = ""

                if item["details_col"] is not None:
                    raw_details = row.iloc[item["details_col"]]
                    if pd.notna(raw_details):
                        details = str(raw_details).strip()

                net_price = None

                if item["net_price_col"] is not None:
                    net_price = ImportHelpers.clean_decimal(
                        row.iloc[item["net_price_col"]]
                    )

                CompanyDiscount.objects.create(

                    profile=profile,

                    section="خارجي",

                    item_name=item["name"],

                    discount=discount,

                    details=details,

                    net_price=net_price,

                    display_order=order,

                    is_active=True,

                )

                result["created_discounts"] += 1

                order += 1

            # ==========================================
            # الاستثناءات الخارجية
            # ==========================================

            external_exception = ImportHelpers.normalize_text(
                row.iloc[44]
            )

            CompanyDiscount.objects.create(

                profile=profile,

                section="خارجي",

                item_name="الاستثناءات",

                details=external_exception,

                display_order=100,

                is_active=True,

            )

            result["created_discounts"] += 1

            i += 7

        return result