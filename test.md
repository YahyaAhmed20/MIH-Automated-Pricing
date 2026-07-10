class CompanyDiscountRank(models.Model):

    company_name = models.CharField(
        max_length=255,
        db_index=True
    )

    financial_category = models.CharField(
        max_length=100
    )

    price_list = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    internal_discount = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0
    )

    external_discount = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0
    )

    attachment = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = [
            "-internal_discount",
            "-external_discount",
            "company_name",
        ]

    def __str__(self):
        return self.company_name
    
    
class CompanyException(models.Model):

    entity_name = models.CharField(
        max_length=255,
        db_index=True
    )

    financial_category = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    price_list = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # ✅ القسم الداخلي
    internal_discount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="معدل الخصم الداخلي"
    )

    internal_details = models.TextField(
        blank=True,
        null=True,
        help_text="تفاصيل الخصم الداخلي"
    )

    # ✅ القسم الخارجي
    external_discount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="معدل الخصم الخارجي"
    )

    external_details = models.TextField(
        blank=True,
        null=True,
        help_text="تفاصيل الخصم الخارجي"
    )

    attachment = models.TextField(
        blank=True,
        null=True,
        help_text="رابط المرفقات"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entity_name"]
        verbose_name = "استثناءات الشركة"
        verbose_name_plural = "استثناءات الشركات"

    def __str__(self):
        return self.entity_name   def company_discounts(request):

    search = request.GET.get(
        "search",
        ""
    )
    entity_id = request.GET.get(
        "entity"
    )

    section = request.GET.get(
        "section",
        ""
    )
    
    active_tab = request.GET.get(
        "tab",
        "discounts"
    )
    
    # ============================================
    # ✅ Tab 2: مقارنة بين جهتين
    # ============================================
    compare_company_1 = request.GET.get(
        "company1",
        ""
    )

    compare_company_2 = request.GET.get(
        "company2",
        ""
    )

    compare_section = request.GET.get(
        "compare_section",
        "all"
    )
    
    selected_company = None

    if entity_id:

        from contracts.models import ContractEntity

        selected_company = get_object_or_404(
            ContractEntity,
            pk=entity_id
        )

        search = selected_company.name

    companies = (
        CompanyDiscountProfile.objects.prefetch_related(
            Prefetch(
                "discounts",
                queryset=CompanyDiscount.objects.order_by(
                    "section",
                    "display_order",
                ),
            )
        ).order_by(
            "company_name"
        )
    )

    if search:

        companies = companies.filter(

            Q(company_name__icontains=search)

            |

            Q(financial_category__icontains=search)

        )

    company_cards = []

    for company in companies:

        internal = []

        external = []

        for discount in company.discounts.all():

            if section == "internal":

                if discount.section != "داخلي":
                    continue

            elif section == "external":

                if discount.section != "خارجي":
                    continue

            if discount.section == "داخلي":

                internal.append(discount)

            else:

                external.append(discount)

        company.internal_discounts = internal

        company.external_discounts = external

        company_cards.append(company)

    # ============================================
    # ✅ قائمة الشركات للـ Dropdown
    # ============================================
    company_names = (
        CompanyDiscountProfile.objects
        .values_list(
            "company_name",
            flat=True
        )
        .distinct()
        .order_by("company_name")
    )

    # ============================================
    # ✅ جلب بيانات الشركتين للمقارنة
    # ============================================
    company_1 = None
    company_2 = None

    if compare_company_1:
        company_1 = (
            CompanyDiscountProfile.objects
            .prefetch_related(
                Prefetch(
                    "discounts",
                    queryset=CompanyDiscount.objects.order_by(
                        "section",
                        "display_order",
                    ),
                )
            )
            .filter(company_name=compare_company_1)
            .first()
        )

    if compare_company_2:
        company_2 = (
            CompanyDiscountProfile.objects
            .prefetch_related(
                Prefetch(
                    "discounts",
                    queryset=CompanyDiscount.objects.order_by(
                        "section",
                        "display_order",
                    ),
                )
            )
            .filter(company_name=compare_company_2)
            .first()
        )

    # ============================================
    # ✅ بناء بيانات المقارنة
    # ============================================
    comparison_rows = (
        CompanyComparisonService.build_comparison(
            company_1,
            company_2,
            compare_section,
        )
    )

    # ============================================
    # ✅ Tab 3: الأعلى والأقل خصماً
    # ============================================
    from pricing_requests.models import CompanyDiscountRank

    rankings = CompanyDiscountRank.objects.all()

    # ============================================
    # ✅ Tab 4: الاستثناءات
    # ============================================
    from pricing_requests.models import CompanyException

    exceptions = CompanyException.objects.all()
    
    # ============================================
    # ✅ القائمة الثابتة للخدمات غير الخاضعة للخصم
    # ============================================
    EXCEPTIONS_LIST = [
        "جميع خدمات بنك الدم",
        "الأدوية والمستلزمات الطبية",
        "الغازات الطبية والأجهزة الطبية المؤجرة من الخارج",
        "أتعاب الأطباء والإشراف الطبي",
        "الاتفاقيات الشاملة",
        "الخدمة الطبية 15% والدمغة الطبية",
        "قسم التخدير وعلاج الآلام",
        "الأشعة التداخلية",
        "خدمات الإسعاف",
        "وحدة الكلى الصناعي",
        "خدمات الفحص الشامل والاستشارات المنزلية",
        "خدمات قسم المبتسرين",
        "المرافق",
        "جميع الخدمات التي تتم خارج المستشفى",
        "وحدة العزل",
        "العلاج الإشعاعي",
        "التركيبات الصناعية للأسنان"
    ]

    return render(

        request,

        "frontend/company_discounts.html",

        {

            "companies": company_cards,

            "search": search,

            "selected_section": section,

            "results_count": len(company_cards),
            "selected_company": selected_company,
            "entity_id": entity_id,
            "active_tab": active_tab,

            # ✅ Tab 2: مقارنة بين جهتين
            "company_names": company_names,
            "compare_company_1": compare_company_1,
            "compare_company_2": compare_company_2,
            "compare_section": compare_section,
            "company_1": company_1,
            "company_2": company_2,
            "comparison_rows": comparison_rows,

            # ✅ Tab 3: الأعلى والأقل خصماً
            "rankings": rankings,

            # ✅ Tab 4: الاستثناءات
            "exceptions": exceptions,
            
            # ✅ القائمة الثابتة للخدمات غير الخاضعة للخصم
            "exceptions_list": EXCEPTIONS_LIST,

        }

    )
   from django.db import transaction
import pandas as pd

from pricing_requests.models import CompanyException

from imports.utils.import_helpers import ImportHelpers


class CompanyExceptionImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        # ✅ متغيرات لتخزين بيانات الجهة الحالية
        current_entity = None
        current_financial = None
        current_price_list = None
        current_internal_discount = None
        current_internal_details = None
        current_external_discount = None
        current_external_details = None
        current_attachment = None

        for _, row in dataframe.iterrows():

            # ✅ قراءة البيانات
            entity_name = ImportHelpers.normalize_text(
                row.get("الجهه")
            )

            financial_category = ImportHelpers.normalize_text(
                row.get("الفئه الماليه")
            )

            price_list = ImportHelpers.normalize_text(
                row.get("قائمة الاسعار")
            )

            # ✅ قراءة الخصومات الداخلية
            internal_discount_raw = row.get("معدل الخصم")
            internal_details_raw = row.get("التفاصيل")

            # ✅ قراءة الخصومات الخارجية
            external_discount_raw = row.get("معدل الخصم.1")
            external_details_raw = row.get("التفاصيل.1")

            attachment = ImportHelpers.normalize_text(
                row.get("صورة العقد")
            )

            # ✅ تنظيف الخصومات
            if pd.notna(internal_discount_raw):
                try:
                    internal_discount = float(internal_discount_raw) * 100
                except:
                    internal_discount = 0
            else:
                internal_discount = 0

            if pd.notna(external_discount_raw):
                try:
                    external_discount = float(external_discount_raw) * 100
                except:
                    external_discount = 0
            else:
                external_discount = 0

            # ✅ تنظيف التفاصيل
            internal_details = ImportHelpers.normalize_text(internal_details_raw) if pd.notna(internal_details_raw) else ""
            external_details = ImportHelpers.normalize_text(external_details_raw) if pd.notna(external_details_raw) else ""

            # ✅ إذا كان الصف يحتوي على جهة جديدة
            if entity_name:
                current_entity = entity_name
                current_financial = financial_category
                current_price_list = price_list
                current_internal_discount = internal_discount
                current_internal_details = internal_details
                current_external_discount = external_discount
                current_external_details = external_details
                current_attachment = attachment

                result["processed"] += 1

                obj, created = CompanyException.objects.update_or_create(
                    entity_name=current_entity,
                    defaults={
                        "financial_category": current_financial,
                        "price_list": current_price_list,
                        "internal_discount": current_internal_discount,
                        "internal_details": current_internal_details,
                        "external_discount": current_external_discount,
                        "external_details": current_external_details,
                        "attachment": current_attachment,
                    }
                )

                if created:
                    result["created"] += 1
                else:
                    result["updated"] += 1

            # ✅ إذا كان الصف يحتوي على تفاصيل إضافية لنفس الجهة
            elif current_entity:
                # ✅ تحديث التفاصيل إذا كانت موجودة
                if internal_details or external_details:
                    result["processed"] += 1

                    # ✅ تجميع التفاصيل معاً
                    if internal_details:
                        current_internal_details = current_internal_details + "\n" + internal_details if current_internal_details else internal_details

                    if external_details:
                        current_external_details = current_external_details + "\n" + external_details if current_external_details else external_details

                    obj, created = CompanyException.objects.update_or_create(
                        entity_name=current_entity,
                        defaults={
                            "financial_category": current_financial,
                            "price_list": current_price_list,
                            "internal_discount": current_internal_discount,
                            "internal_details": current_internal_details,
                            "external_discount": current_external_discount,
                            "external_details": current_external_details,
                            "attachment": current_attachment,
                        }
                    )

                    if created:
                        result["created"] += 1
                    else:
                        result["updated"] += 1

        return result from django.core.management.base import BaseCommand

import pandas as pd

from imports.services.company_exception_import_service import (
    CompanyExceptionImportService,
)


class Command(BaseCommand):

    help = "Import Company Exceptions from Excel Sheet 9"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Company Exceptions Import =========="
        )

        # ✅ قراءة الشيت
        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="9",
            header=2,
        )

        # ✅ عرض الأعمدة للتأكد
        print("📋 أسماء الأعمدة:")
        print(dataframe.columns.tolist())
        print("=" * 50)

        # ✅ إعادة تسمية الأعمدة المهمة فقط
        dataframe = dataframe.rename(
            columns={
                "Unnamed: 0": "الجهه",
                "Unnamed: 1": "الفئه الماليه",
                "Unnamed: 2": "قائمة الاسعار",
                "معدل الخصم": "معدل الخصم_داخلي",
                "التفاصيل ": "التفاصيل_داخلي",
                "معدل الخصم.1": "معدل الخصم_خارجي",
                "التفاصيل وصافي السعر": "التفاصيل_خارجي",
                "Unnamed: 7": "سعر_الخدمة",
                "Unnamed: 29": "المرفقات",
            }
        )

        # ✅ حذف الصفوف الفارغة
        dataframe = dataframe[
            dataframe["الجهه"].notna()
        ]

        # ✅ إعادة تعيين الـ Index
        dataframe = dataframe.reset_index(drop=True)

        print(f"📊 عدد الصفوف: {len(dataframe)}")

        result = (
            CompanyExceptionImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            f"Processed : {result['processed']}"
        )

        self.stdout.write(
            f"Created   : {result['created']}"
        )

        self.stdout.write(
            f"Updated   : {result['updated']}"
        )

        self.stdout.write(
            f"Skipped   : {result['skipped']}"
        )

        self.stdout.write(
            "==========================================="
        )