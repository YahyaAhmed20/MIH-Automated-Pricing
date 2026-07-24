from xml.dom.minidom import Entity

from django.db.models.functions import TruncMonth
from contracts.services.pricing_engine import PricingEngine
from django.db.models import Count
from contracts.models import ContractPackage
from django.db.models import Count
from contracts.models import (
    CompanyDiscountProfile,
)
from frontend.services.company_comparison_service import (
    CompanyComparisonService,
)
from pricing_requests.models import Procedure
from django.db.models import Q, Sum, Avg
from pricing_requests.models import PricingDetail
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.core.paginator import Paginator

from pricing_requests.models import SimilarInvoice

from pricing_requests.models import ServiceRecord
from django.db.models import Sum
from django.core.paginator import Paginator

from frontend.services.special_offers_service import (
    SpecialOffersService,
)
from django.db.models import Q, Prefetch

from contracts.models import (
    CompanyDiscountProfile,
    CompanyDiscount,
)
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from pricing_requests.models import PricingRequest
import json
from django.db.models import Sum, Avg, Count, F
from django.shortcuts import render
import json
from django.db.models import Sum, Avg, Count, F
from django.shortcuts import render
from pricing_requests.models import PricingRequest
from django.core.paginator import Paginator
from django.db.models import Avg
from contracts.models import ContractPackage
from django.db.models import Count, Sum, Avg, F
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, F
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Avg
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Avg, Count
from django.db.models import Sum, Avg, Count
from django.shortcuts import render, get_object_or_404
from datetime import date
from django.db.models import Avg, Count, Q
from django.shortcuts import render

from django.db.models import Count, Avg
from pricing_requests.models import PricingRequest

from django.db.models import Q
from django.db.models import Sum, Avg, Count, F
from pricing_requests.models import PricingRequest
from contracts.models import ContractEntity
from medical_catalog.models import Specialty
from django.core.paginator import Paginator
from django.db.models import Q
from contracts.models import ContractEntity, ContractPackage
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from pricing_requests.models import PricingRequest
from pricing_requests.models import (
    Patient,
    PricingRequest,
    PricingRequestNote
)
from medical_catalog.models import Package
from django.core.paginator import Paginator
from django.db.models import Q
from contracts.models import Contract
# Create your views here.
# frontend/views.py
from django.shortcuts import redirect
from django.contrib import messages

from django.db.models import Sum, Count
from django.db.models import Count
from contracts.models import ContractEntity
from pricing_requests.models import PricingRequest
from django.db.models import Sum, Count
from django.shortcuts import render

def home(request):

    total_requested = (
        PricingRequest.objects.aggregate(
            total=Sum("requested_cost")
        )["total"] or 0
    )

    total_received = (
        PricingRequest.objects.aggregate(
            total=Sum("received_cost")
        )["total"] or 0
    )

    difference = total_requested - total_received

    top_pending_entities = (
        PricingRequest.objects
        .filter(status="pending")
        .values("entity__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    top_pending_doctors = (
        PricingRequest.objects
        .filter(status="pending")
        .values("doctor_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # ✅ أعلى جهة استخداماً (جديد)
    top_entity = (
        PricingRequest.objects
        .values("entity__name")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )

    # ✅ أكثر طبيب نشاطاً (جديد)
    top_doctor = (
        PricingRequest.objects
        .exclude(doctor_name="")
        .values("doctor_name")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )

    context = {

        "patients": Patient.objects.count(),
        "requests": PricingRequest.objects.count(),
        "notes": PricingRequestNote.objects.count(),
        "contracts": Contract.objects.count(),

        "approved":
            PricingRequest.objects.filter(
                status="approved"
            ).count(),

        "pending":
            PricingRequest.objects.filter(
                status="pending"
            ).count(),

        "rejected":
            PricingRequest.objects.filter(
                status="rejected"
            ).count(),

        "service_done":
            PricingRequest.objects.filter(
                status="service_done"
            ).count(),

        "latest_requests":
            PricingRequest.objects
            .select_related(
                "patient",
                "entity",
                "specialty"
            )
            .order_by("-id")[:10],

        # Executive Dashboard - ✅ مع تنسيق الأرقام بفواصل
        "total_requested": f"{total_requested:,.0f}",
        "total_received": f"{total_received:,.0f}",
        "difference": f"{difference:,.0f}",

        "top_pending_entities":
            top_pending_entities,

        "top_pending_doctors":
            top_pending_doctors,

        # ✅ أعلى جهة وأكثر طبيب (جديد)
        "top_entity": top_entity,
        "top_doctor": top_doctor,
    }

    return render(
        request,
        "frontend/home.html",
        context
    )


def packages(request):

    search = request.GET.get("search", "")
    package_type = request.GET.get("type", "")
    specialty = request.GET.get("specialty", "")

    packages = Package.objects.select_related(
        "specialty"
    )

    # لو الصفحة النقدي
    if request.path == "/cash-packages/":
        packages = packages.filter(
            is_cash_package=True
        )
    else:
        packages = packages.order_by("name")

    # البحث
    if search:
        packages = packages.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    # فلتر النوع (جديد)
    if package_type == "cash":
        packages = packages.filter(is_cash_package=True)
    elif package_type == "credit":
        packages = packages.filter(is_cash_package=False)

    # فلتر التخصص
    if specialty:
        packages = packages.filter(
            specialty__id=specialty
        )

    paginator = Paginator(packages, 20)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    specialties = Specialty.objects.filter(
        is_active=True
    ).order_by("name")

    return render(
        request,
        "frontend/packages.html",
        {
            "page_obj": page_obj,
            "search": search,
            "package_type": package_type,
            "specialties": specialties,
            "selected_specialty": specialty,
        }
    )

# views.py
def package_create(request):
    # مجرد عرض رسالة
    messages.info(request, 'سيتم إضافة صفحة إضافة الباكدج قريباً 📦')
    return redirect('frontend:packages')

def contracts(request):
    return render(
        request,
        "frontend/contracts.html"
    )


def discounts(request):
    return render(
        request,
        "frontend/discounts.html"
    )


def offers(request):
    return render(
        request,
        "frontend/offers.html"
    )


def operations(request):
    return render(
        request,
        "frontend/operations.html"
    )





def approvals(request):
    return render(
        request,
        "frontend/approvals.html"
    )




def price_lists(request):
    return render(
        request,
        "frontend/price_lists.html"
    )
    
    




def contract_entities(request):

    search = request.GET.get("search", "")
    
    # ✅ اجلب فقط الجهات اللي عندها عقود نشطة وخدمة طبية (نفس تصفية الجدول)
    all_entities = ContractEntity.objects.filter(
        contracts__is_active=True,
        contracts__medical_service__isnull=False,
    ).exclude(
        contracts__medical_service=""
    ).distinct().order_by("name")

    contracts = (
        Contract.objects.select_related(
            "entity",
            "financial_category",
            "price_list",
        )
        .filter(
            is_active=True,
            medical_service__isnull=False,
        )
        .exclude(
            medical_service=""
        )
        .order_by("entity__name")
    )

    # ==========================================
    # Search
    # ==========================================

    if search:

        contracts = contracts.filter(

            Q(entity__name__icontains=search)

            |

            Q(financial_category__code__icontains=search)

        )

    return render(

        request,

        "frontend/contract_entities.html",

        {
            "all_entities": all_entities,
            "contracts": contracts,

            "search": search,

            "results_count": contracts.count(),

        }

    )
# frontend/views.py

from datetime import timedelta


def external_approvals(request):
    """
    صفحة متابعة موافقات الخارجي - شيت 12
    عرض 6 بوكسات إحصائية + توزيع الحالات
    """
    
    all_records = ExternalApproval.objects.all()
    total_cases = all_records.count()
    
    # ✅ الإحصائيات
    approval_count = all_records.exclude(approval__isnull=True).exclude(approval="").count()
    billing_count = all_records.exclude(billing_status__isnull=True).exclude(billing_status="").count()
    
    pending_accounts = max(approval_count - billing_count, 0)
    pending_coordinator = all_records.exclude(billing_status__isnull=True).exclude(billing_status="").filter(admission_date__isnull=True).count()
    cases_without_approval = max(total_cases - approval_count, 0)
    
    today = timezone.localtime().date()
    tomorrow = today + timedelta(days=1)
    early_admissions = all_records.filter(admission_date=tomorrow).count()
    
    # ✅ توزيع الحالات حسب Main Status
    status_distribution = (
        all_records
        .values("main_status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    defined_status_count = all_records.exclude(main_status__isnull=True).exclude(main_status="").count()
    undefined_status = total_cases - defined_status_count
    
    status_colors = {
        "Approved": "#28a745",
        "Pending": "#ffc107",
        "Rejected": "#dc3545",
        "Serv. Done": "#17a2b8",
        "Patient refused": "#6c757d",
        "غير محدد": "#6c757d",
    }
    
    status_data = []
    for item in status_distribution:
        status_name = item["main_status"] or "غير محدد"
        count = item["count"]
        percentage = round((count / total_cases) * 100, 1) if total_cases > 0 else 0
        status_data.append({
            "name": status_name,
            "count": count,
            "percentage": percentage,
            "color": status_colors.get(status_name, "#6c757d"),
        })
    
    if undefined_status > 0:
        found = False
        for item in status_data:
            if item["name"] == "غير محدد":
                item["count"] = undefined_status
                item["percentage"] = round((undefined_status / total_cases) * 100, 1) if total_cases > 0 else 0
                item["color"] = status_colors["غير محدد"]
                found = True
                break
        if not found:
            status_data.append({
                "name": "غير محدد",
                "count": undefined_status,
                "percentage": round((undefined_status / total_cases) * 100, 1) if total_cases > 0 else 0,
                "color": status_colors["غير محدد"],
            })
    
    box_colors = {
        "total": "linear-gradient(135deg, #1a237e, #0d47a1)",
        "without_approval": "linear-gradient(135deg, #6a1b9a, #8e24aa)",
        "accounts": "linear-gradient(135deg, #b71c1c, #d32f2f)",
        "coordinator": "linear-gradient(135deg, #e65100, #f57c00)",
        "early": "linear-gradient(135deg, #1b5e20, #2e7d32)",
        "overview": "linear-gradient(135deg, #4a148c, #6a1b9a)",
    }
    
    context = {
        'total_cases': total_cases,
        'cases_without_approval': cases_without_approval,
        'pending_accounts': pending_accounts,
        'pending_coordinator': pending_coordinator,
        'early_admissions': early_admissions,
        'status_data': status_data,
        'box_colors': box_colors,
    }
    
    return render(request, 'frontend/external_approvals.html', context)


# frontend/views.py

def external_approvals_detail(request, filter_type):
    """صفحة تفاصيل الموافقات الخارجية"""
    
    all_records = ExternalApproval.objects.all()
    total_cases = all_records.count()
    
    # ✅ الفلتر حسب النوع
    if filter_type == "total":
        patients = all_records
        title = "إجمالي الحالات المرسلة للتسعير"
    elif filter_type == "accounts":
        patients = all_records.filter(
            ~Q(approval__isnull=True) & ~Q(approval=''),
            Q(billing_status__isnull=True) | Q(billing_status='')
        )
        title = "الحالات المعطلة طرف الحسابات"
    elif filter_type == "coordinator":
        patients = all_records.exclude(billing_status__isnull=True).exclude(billing_status="").filter(admission_date__isnull=True)
        title = "الحالات المعطلة طرف منسق العيادات"
    elif filter_type == "without_approval":
        patients = all_records.filter(Q(approval__isnull=True) | Q(approval=''))
        title = "حالات بدون موافقة"
    elif filter_type == "early":
        today = timezone.localtime().date()
        tomorrow = today + timedelta(days=1)
        patients = all_records.filter(admission_date=tomorrow)
        title = "حالات دخول باكر (غداً)"
    else:
        patients = all_records
        title = "جميع الحالات"
    
    # ✅ البحث والفلاتر
    search_query = request.GET.get("search", "")
    attachment_type = request.GET.get("attachment_type", "")
    company_filter = request.GET.get("company", "")
    sub_account_filter = request.GET.get("sub_account", "")
    doctor_filter = request.GET.get("doctor", "")
    specialty_filter = request.GET.get("specialty", "")
    main_status_filter = request.GET.get("main_status", "")  # ✅ NEW
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    
    # ✅ تطبيق الفلاتر
    if search_query:
        patients = patients.filter(
            Q(patient_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(card_number__icontains=search_query) |
            Q(medical_number__icontains=search_query) |
            Q(account_number__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(sub_account__icontains=search_query)
        )
    
    if attachment_type:
        patients = patients.filter(attachment_type__icontains=attachment_type)
    if company_filter:
        patients = patients.filter(company__icontains=company_filter)
    if sub_account_filter:
        patients = patients.filter(sub_account__icontains=sub_account_filter)
    if doctor_filter:
        patients = patients.filter(doctor_name__icontains=doctor_filter)
    if specialty_filter:
        patients = patients.filter(specialty__icontains=specialty_filter)
    if main_status_filter:  # ✅ NEW
        patients = patients.filter(main_status__icontains=main_status_filter)
    if date_from:
        try:
            patients = patients.filter(date__gte=date_from)
        except:
            pass
    if date_to:
        try:
            patients = patients.filter(date__lte=date_to)
        except:
            pass
    
    # ✅ Pagination
    paginator = Paginator(patients, 50)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # ✅ قيم الفلاتر
    filter_queryset = patients
    
    attachment_types = list(
        filter_queryset
        .values_list('attachment_type', flat=True)
        .distinct()
        .exclude(attachment_type__isnull=True)
        .exclude(attachment_type='')
        .order_by('attachment_type')
    )
    
    companies = list(
        filter_queryset
        .values_list('company', flat=True)
        .distinct()
        .exclude(company__isnull=True)
        .exclude(company='')
        .order_by('company')
    )
    
    sub_accounts = list(
        filter_queryset
        .values_list('sub_account', flat=True)
        .distinct()
        .exclude(sub_account__isnull=True)
        .exclude(sub_account='')
        .order_by('sub_account')
    )
    
    doctors = list(
        filter_queryset
        .values_list('doctor_name', flat=True)
        .distinct()
        .exclude(doctor_name__isnull=True)
        .exclude(doctor_name='')
        .order_by('doctor_name')
    )
    
    specialties = list(
        filter_queryset
        .values_list('specialty', flat=True)
        .distinct()
        .exclude(specialty__isnull=True)
        .exclude(specialty='')
        .order_by('specialty')
    )
    
    # ✅ NEW: قيم Main Status للفلتر
    main_statuses = list(
        filter_queryset
        .values_list('main_status', flat=True)
        .distinct()
        .exclude(main_status__isnull=True)
        .exclude(main_status='')
        .order_by('main_status')
    )
    
    context = {
        'title': title,
        'search_query': search_query,
        'patients': page_obj,
        'patient_count': patients.count(),
        'attachment_type': attachment_type,
        'company_filter': company_filter,
        'sub_account_filter': sub_account_filter,
        'doctor_filter': doctor_filter,
        'specialty_filter': specialty_filter,
        'main_status_filter': main_status_filter,  # ✅ NEW
        'date_from': date_from,
        'date_to': date_to,
        'attachment_types': attachment_types,
        'companies': companies,
        'sub_accounts': sub_accounts,
        'doctors': doctors,
        'specialties': specialties,
        'main_statuses': main_statuses,  # ✅ NEW
    }
    
    return render(request, 'frontend/external_approvals_detail.html', context)
def approval_detail(request, pk):

    
    approval = get_object_or_404(
        PricingRequest.objects.select_related(
            "patient",
            "entity",
            "specialty"
        ),
        pk=pk
    )

    return render(
        request,
        "frontend/approval_detail.html",
        {
            "approval": approval
        }
    )
from django.db.models import Count, Q
from django.shortcuts import render
from pricing_requests.models import ReportStatistic
import json

SPECIALTIES = [
    "الانف والاذن",
    "الجراحه",          
    "العظام",
    "القسطره وجراحات القلب",
    "القلب المفتوح",
    "الكلي و المسالك البوليه",
    "النساء والتوليد",
    "جراحة المخ والاعصاب",
]


SPECIALTY_ICONS = {
    "الانف والاذن": "fas fa-ear",
    "الجراحه": "fas fa-scalpel",  # ✅ أضف

    "العظام": "fas fa-bone",
    "القسطره وجراحات القلب": "fas fa-heart-pulse",
    "القلب المفتوح": "fas fa-heartbeat",
    "الكلي و المسالك البوليه": "fas fa-kidney",
    "النساء والتوليد": "fas fa-person-pregnant",
    "جراحة المخ والاعصاب": "fas fa-brain",
}


SPECIALTY_COLORS = {
    "الانف والاذن": "#6f42c1",
    "الجراحه": "#0d6efd",  # ✅ أضف (أزرق)

    "العظام": "#fd7e14",
    "القسطره وجراحات القلب": "#dc3545",
    "القلب المفتوح": "#e83e8c",
    "الكلي و المسالك البوليه": "#20c997",
    "النساء والتوليد": "#ff6b6b",
    "جراحة المخ والاعصاب": "#4dabf7",
}


MONTH_ORDER = [
    "يناير",
    "فبراير",
    "مارس",
    "ابريل",
    "مايو",
    "يونيو",
    "يوليو",
    "اغسطس",
    "سبتمبر",
    "اكتوبر",
    "نوفمبر",
    "ديسمبر",
]


def reports_statistics(request):

    selected_month = request.GET.get("month", "")

    statistics = ReportStatistic.objects.all()

    if selected_month:
        statistics = statistics.filter(month=selected_month)

    months_raw = list(
        ReportStatistic.objects.values_list(
            "month",
            flat=True
        ).distinct()
    )

    months = [
        month
        for month in MONTH_ORDER
        if month in months_raw
    ]

    total_packages = statistics.count()

    cash_packages = statistics.filter(
        payment_type="نقدي"
    ).count()

    credit_packages = statistics.filter(
        payment_type="اجل"
    ).count()

    # ============================================
    # Payment Type Statistics - النسب المئوية
    # ============================================
    
    if total_packages > 0:
        cash_percentage = round(
            (cash_packages / total_packages) * 100,
            1
        )
        
        credit_percentage = round(
            (credit_packages / total_packages) * 100,
            1
        )
    else:
        cash_percentage = 0
        credit_percentage = 0

    # ============================================
    # Packages By Sector (Credit Only)
    # ============================================
    
    sector_statistics = (
        statistics
        .filter(payment_type="اجل")
        .values("sector")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    
    sector_data = []
    
    for row in sector_statistics:
        
        percentage = 0
        
        if credit_packages > 0:
            
            percentage = round(
                (row["total"] / credit_packages) * 100,
                1
            )
        
        sector_data.append({
            
            "name": row["sector"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })

    # ============================================
    # Sector Chart Data - جاهز للـ Doughnut Chart
    # ============================================
    
    sector_labels = json.dumps(
        [item["name"] for item in sector_data],
        ensure_ascii=False
    )
    
    sector_values = json.dumps(
        [item["total"] for item in sector_data]
    )
    
    sector_colors = json.dumps([
        "#0d6efd",
        "#20c997",
        "#ffc107",
        "#dc3545",
        "#6f42c1",
        "#fd7e14",
        "#198754",
        "#6610f2",
        "#0dcaf0",
        "#6c757d",
    ])

    # ============================================
    # Top & Bottom 5 Entities (Credit Only)
    # ============================================
    
    entity_statistics = (
        statistics
        .filter(payment_type="اجل")
        .values("entity_name")
        .annotate(total=Count("id"))
    )
    
    # أعلى 5 جهات
    top_entities = []
    
    for row in entity_statistics.order_by("-total")[:5]:
        
        percentage = 0
        
        if credit_packages > 0:
            percentage = round(
                (row["total"] / credit_packages) * 100,
                1
            )
        
        top_entities.append({
            
            "name": row["entity_name"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })
    
    # أقل 5 جهات
    bottom_entities = []
    
    for row in entity_statistics.order_by("total", "entity_name")[:5]:
        
        percentage = 0
        
        if credit_packages > 0:
            percentage = round(
                (row["total"] / credit_packages) * 100,
                1
            )
        
        bottom_entities.append({
            
            "name": row["entity_name"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })

    # ============================================
    # Top & Bottom 5 Sub Companies (Credit Only)
    # ============================================
    
    sub_company_statistics = (
        statistics
        .filter(payment_type="اجل")
        .exclude(sub_company="")
        .exclude(sub_company__isnull=True)
        .values("sub_company")
        .annotate(total=Count("id"))
    )
    
    # أعلى 5 شركات فرعية
    top_sub_companies = []
    
    for row in sub_company_statistics.order_by("-total")[:5]:
        
        percentage = 0
        
        if credit_packages > 0:
            percentage = round(
                (row["total"] / credit_packages) * 100,
                1
            )
        
        top_sub_companies.append({
            
            "name": row["sub_company"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })
    
    # أقل 5 شركات فرعية
    bottom_sub_companies = []
    
    for row in sub_company_statistics.order_by("total", "sub_company")[:5]:
        
        percentage = 0
        
        if credit_packages > 0:
            percentage = round(
                (row["total"] / credit_packages) * 100,
                1
            )
        
        bottom_sub_companies.append({
            
            "name": row["sub_company"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })

    # ============================================
    # Top & Bottom 5 Specialties
    # ============================================
    
    specialty_statistics = (
        statistics
        .exclude(specialty="")
        .exclude(specialty__isnull=True)
        .values("specialty")
        .annotate(total=Count("id"))
    )
    
    # أعلى 5 تخصصات
    top_specialties = []
    
    for row in specialty_statistics.order_by("-total")[:5]:
        
        percentage = 0
        
        if total_packages > 0:
            
            percentage = round(
                (row["total"] / total_packages) * 100,
                1
            )
        
        top_specialties.append({
            
            "name": row["specialty"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })
    
    # أقل 5 تخصصات
    bottom_specialties = []
    
    for row in specialty_statistics.order_by("total", "specialty")[:5]:
        
        percentage = 0
        
        if total_packages > 0:
            
            percentage = round(
                (row["total"] / total_packages) * 100,
                1
            )
        
        bottom_specialties.append({
            
            "name": row["specialty"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })

    # ============================================
    # Top & Bottom 5 Packages
    # ============================================
    
    package_statistics = (
        statistics
        .exclude(package_name="")
        .exclude(package_name__isnull=True)
        .values("package_name")
        .annotate(total=Count("id"))
    )
    
    # أعلى 5 باكدجات
    top_packages = []
    
    for row in package_statistics.order_by("-total")[:5]:
        
        percentage = 0
        
        if total_packages > 0:
            percentage = round(
                (row["total"] / total_packages) * 100,
                1
            )
        
        top_packages.append({
            
            "name": row["package_name"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })
    
    # أقل 5 باكدجات
    bottom_packages = []
    
    for row in package_statistics.order_by("total", "package_name")[:5]:
        
        percentage = 0
        
        if total_packages > 0:
            percentage = round(
                (row["total"] / total_packages) * 100,
                1
            )
        
        bottom_packages.append({
            
            "name": row["package_name"],
            
            "total": row["total"],
            
            "percentage": percentage,
            
        })

    specialty_summary = {
        row["specialty"]: row
        for row in (
            statistics
            .values("specialty")
            .annotate(
                total=Count("id"),
                cash=Count(
                    "id",
                    filter=Q(payment_type="نقدي"),
                ),
                credit=Count(
                    "id",
                    filter=Q(payment_type="اجل"),
                ),
            )
        )
    }

    chart_data = {}

    for specialty in SPECIALTIES:

        monthly = (
            statistics
            .filter(specialty__icontains=specialty)  # ✅ استخدم __icontains
            .values("month")
            .annotate(total=Count("id"))
            .order_by()
        )

        chart_data[specialty] = {
            row["month"]: row["total"]
            for row in monthly
        }

    specialties = []

    for specialty in SPECIALTIES:

        row = specialty_summary.get(specialty, {})

        chart_sorted = {}

        for month in MONTH_ORDER:
            if month in chart_data.get(specialty, {}):
                chart_sorted[month] = chart_data[specialty][month]

        # ✅ ✅ ✅ جلب السجلات التفصيلية لكل تخصص
        specialty_records = statistics.filter(specialty__icontains=specialty)
        
        records_list = specialty_records.values(
            'account_number',
            'patient_name',
            'admission_date',
            'discharge_date',
            'package_name',
            'entity_name',
            'sub_company',
            'amount',
            'month',
        ).order_by('-admission_date')  # ✅ حد أقصى 50 سجل

        specialties.append({

            "name": specialty,

            "icon": SPECIALTY_ICONS.get(
                specialty,
                "fas fa-stethoscope"
            ),

            "color": SPECIALTY_COLORS.get(
                specialty,
                "#6c757d"
            ),

            "total": row.get("total", 0),

            "cash": row.get("cash", 0),

            "credit": row.get("credit", 0),

            "chart_labels": json.dumps(
                list(chart_sorted.keys()),
                ensure_ascii=False
            ),

            "chart_values": json.dumps(
                list(chart_sorted.values())
            ),

            "records": list(records_list),  # ✅ السجلات التفصيلية

        })

    return render(
        request,
        "frontend/reports.html",
        {
            "months": months,
            "selected_month": selected_month,
            "total_packages": total_packages,
            "cash_packages": cash_packages,
            "credit_packages": credit_packages,
            "cash_percentage": cash_percentage,
            "credit_percentage": credit_percentage,
            "sector_data": sector_data,
            "sector_labels": sector_labels,
            "sector_values": sector_values,
            "sector_colors": sector_colors,
            "top_entities": top_entities,
            "bottom_entities": bottom_entities,
            "top_sub_companies": top_sub_companies,
            "bottom_sub_companies": bottom_sub_companies,
            "top_specialties": top_specialties,
            "bottom_specialties": bottom_specialties,
            "top_packages": top_packages,
            "bottom_packages": bottom_packages,
            "specialties": specialties,
        },
    )
    
    
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from pricing_requests.models import ReportStatistic
import json
from django.core.paginator import Paginator

# التخصص
def specialty_detail(request, specialty_name):
    """صفحة تفاصيل التخصص - عرض جميع السجلات"""
    
    # ✅ الفلتر (الشهر)
    selected_month = request.GET.get("month", "")
    
    # ✅ البحث (الباكدج)
    package_search = request.GET.get("package_search", "")
    
    # ✅ البحث (الجهة)
    entity_search = request.GET.get("entity_search", "")
    
    # ✅ جلب السجلات الخاصة بالتخصص
    records = ReportStatistic.objects.filter(specialty__icontains=specialty_name)
    
    if selected_month:
        records = records.filter(month=selected_month)
    
    if package_search:
        records = records.filter(package_name__icontains=package_search)
    
    if entity_search:
        records = records.filter(entity_name__icontains=entity_search)
    
    # ✅ إحصائيات التخصص
    total_count = records.count()
    cash_count = records.filter(payment_type="نقدي").count()
    credit_count = records.filter(payment_type="اجل").count()
    total_amount = records.aggregate(total=Sum('amount'))['total'] or 0
    
    # ✅ توزيع العمليات
    package_distribution = (
        records
        .values('package_name')
        .annotate(
            total=Count('id'),
            total_amount=Sum('amount')
        )
        .filter(package_name__isnull=False)
        .exclude(package_name='')
        .order_by('-total')[:20]
    )
    
    total_unique_packages = records.values('package_name').distinct().count()
    
    # ✅ ✅ ✅ توزيع الجهات
    entity_distribution = (
        records
        .values('entity_name')
        .annotate(
            total=Count('id'),
            total_amount=Sum('amount')
        )
        .filter(entity_name__isnull=False)
        .exclude(entity_name='')
        .order_by('-total')[:20]
    )
    
    total_unique_entities = records.values('entity_name').distinct().count()
    
    # ✅ الشهور
    months_raw = list(
        records.values_list('month', flat=True).distinct()
    )
    
    MONTH_ORDER = [
        "يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو",
        "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"
    ]
    
    months = [m for m in MONTH_ORDER if m in months_raw]
    
    # ✅ Pagination
    paginator = Paginator(records.order_by('-admission_date'), 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # ✅ التوزيع حسب نوع الدفع
    payment_distribution = (
        records.values('payment_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    
    # ✅ التوزيع حسب القطاع
    sector_distribution = (
        records.values('sector')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    
    # ✅ قائمة الباكدجات للاقتراحات
    package_suggestions = list(set(
        records
        .values_list('package_name', flat=True)
        .filter(package_name__isnull=False)
        .exclude(package_name='')
    ))[:50]
    
    # ✅ قائمة الجهات للاقتراحات
    entity_suggestions = list(set(
        records
        .values_list('entity_name', flat=True)
        .filter(entity_name__isnull=False)
        .exclude(entity_name='')
    ))[:50]
    
    context = {
        'specialty_name': specialty_name,
        'records': page_obj,
        'total_count': total_count,
        'cash_count': cash_count,
        'credit_count': credit_count,
        'total_amount': total_amount,
        'months': months,
        'selected_month': selected_month,
        'package_search': package_search,
        'entity_search': entity_search,
        'package_suggestions': package_suggestions,
        'entity_suggestions': entity_suggestions,
        'payment_distribution': payment_distribution,
        'sector_distribution': sector_distribution,
        'package_distribution': package_distribution,
        'total_unique_packages': total_unique_packages,
        # ✅ ✅ ✅ جديد
        'entity_distribution': entity_distribution,
        'total_unique_entities': total_unique_entities,
    }
    
    return render(request, 'frontend/specialty_detail.html', context)

# frontend/views.py

from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.core.paginator import Paginator
from pricing_requests.models import ReportStatistic


# frontend/views.py

from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.core.paginator import Paginator
from pricing_requests.models import ReportStatistic

#  الباكجات حسب نوع الدفع

def payment_details(request):
    """صفحة تفاصيل الباكدجات حسب نوع الدفع"""
    
    # ✅ فلتر نوع الدفع
    payment_type = request.GET.get("payment_type", "")
    
    # ✅ فلتر التخصص
    specialty_search = request.GET.get("specialty_search", "")
    
    # ✅ جلب جميع السجلات
    records = ReportStatistic.objects.all()
    
    if payment_type:
        records = records.filter(payment_type=payment_type)
    
    if specialty_search:
        records = records.filter(specialty__icontains=specialty_search)
    
    # ✅ إحصائيات
    total_count = records.count()
    cash_count = records.filter(payment_type="نقدي").count()
    credit_count = records.filter(payment_type="اجل").count()
    total_amount = records.aggregate(total=Sum('amount'))['total'] or 0
    
    # ✅ التوزيع حسب نوع الدفع
    payment_distribution = (
        records.values('payment_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    
    # ✅ التوزيع حسب القطاع (للآجل فقط)
    sector_distribution = (
        records
        .filter(payment_type="اجل")
        .values('sector')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    
    # ✅ ✅ ✅ قائمة التخصصات للاقتراحات (فريدة)
    specialty_suggestions = list(set(
        records
        .values_list('specialty', flat=True)
        .filter(specialty__isnull=False)
        .exclude(specialty='')
    ))[:50]
    
    # ✅ Pagination
    paginator = Paginator(records.order_by('-admission_date'), 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'records': page_obj,
        'total_count': total_count,
        'cash_count': cash_count,
        'credit_count': credit_count,
        'total_amount': total_amount,
        'payment_type': payment_type,
        'specialty_search': specialty_search,
        'payment_distribution': payment_distribution,
        'sector_distribution': sector_distribution,
        'specialty_suggestions': specialty_suggestions,
    }
    
    return render(request, 'frontend/payment_details.html', context)
#  الباكجات حسب القطاع (آجل فقط)

# frontend/views.py

from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.core.paginator import Paginator
from pricing_requests.models import ReportStatistic

# الباكجات حسب القطاع (آجل فقط)
def sector_details(request):
    """صفحة تفاصيل الباكجات حسب القطاع (آجل فقط)"""
    
    # ✅ فلتر القطاع
    sector_search = request.GET.get("sector_search", "")
    
    # ✅ فلتر التخصص
    specialty_search = request.GET.get("specialty_search", "")
    
    # ✅ فلتر الجهة
    entity_search = request.GET.get("entity_search", "")
    
    # ✅ فلتر الشركة الفرعية
    sub_company_search = request.GET.get("sub_company_search", "")
    
    # ✅ فلتر الباكدج
    package_search = request.GET.get("package_search", "")
    
    # ✅ فلتر التاريخ من
    date_from = request.GET.get("date_from", "")
    
    # ✅ فلتر التاريخ إلى
    date_to = request.GET.get("date_to", "")
    
    # ✅ جلب السجلات (آجل فقط)
    records = ReportStatistic.objects.filter(payment_type="اجل")
    
    if sector_search:
        records = records.filter(sector__icontains=sector_search)
    
    if specialty_search:
        records = records.filter(specialty__icontains=specialty_search)
    
    if entity_search:
        records = records.filter(entity_name__icontains=entity_search)
    
    if sub_company_search:
        records = records.filter(sub_company__icontains=sub_company_search)
    
    if package_search:
        records = records.filter(package_name__icontains=package_search)
    
    if date_from:
        try:
            records = records.filter(admission_date__gte=date_from)
        except:
            pass
    
    if date_to:
        try:
            records = records.filter(admission_date__lte=date_to)
        except:
            pass
    
    # ✅ إحصائيات
    total_count = records.count()
    total_amount = records.aggregate(total=Sum('amount'))['total'] or 0
    
    # ✅ التوزيع حسب القطاع
    sector_distribution = (
        records
        .values('sector')
        .annotate(
            total=Count('id'),
            total_amount=Sum('amount')
        )
        .filter(sector__isnull=False)
        .exclude(sector='')
        .order_by('-total')
    )
    
    # ✅ ✅ ✅ التوزيع حسب النقابة (entity_name) داخل القطاع المحدد
    entity_distribution = (
        records
        .values('entity_name')
        .annotate(
            total=Count('id'),
            total_amount=Sum('amount')
        )
        .filter(entity_name__isnull=False)
        .exclude(entity_name='')
        .order_by('-total')
    )
    
    # ✅ ✅ ✅ تجهيز بيانات النقابات مع التخصصات والباكدجات (منظمة)
    entity_details = []
    for entity in entity_distribution:
        entity_name = entity['entity_name']
        
        # التخصصات داخل النقابة
        specialties = (
            records
            .filter(entity_name=entity_name)
            .values('specialty')
            .annotate(
                total=Count('id'),
                total_amount=Sum('amount')
            )
            .filter(specialty__isnull=False)
            .exclude(specialty='')
            .order_by('-total')
        )
        
        # الباكدجات داخل النقابة
        packages = (
            records
            .filter(entity_name=entity_name)
            .values('package_name')
            .annotate(
                total=Count('id'),
                total_amount=Sum('amount')
            )
            .filter(package_name__isnull=False)
            .exclude(package_name='')
            .order_by('-total')
        )
        
        entity_details.append({
            'entity_name': entity_name,
            'total': entity['total'],
            'total_amount': entity['total_amount'],
            'specialties': specialties,
            'packages': packages,
        })
    
    # ✅ قائمة القطاعات للاقتراحات
    sector_suggestions = list(set(
        records
        .values_list('sector', flat=True)
        .filter(sector__isnull=False)
        .exclude(sector='')
    ))[:50]
    
    # ✅ قائمة التخصصات للاقتراحات
    specialty_suggestions = list(set(
        records
        .values_list('specialty', flat=True)
        .filter(specialty__isnull=False)
        .exclude(specialty='')
    ))[:50]
    
    # ✅ قائمة الجهات للاقتراحات
    entity_suggestions = list(set(
        records
        .values_list('entity_name', flat=True)
        .filter(entity_name__isnull=False)
        .exclude(entity_name='')
    ))[:50]
    
    # ✅ قائمة الشركات الفرعية للاقتراحات
    sub_company_suggestions = list(set(
        records
        .values_list('sub_company', flat=True)
        .filter(sub_company__isnull=False)
        .exclude(sub_company='')
    ))[:50]
    
    # ✅ قائمة الباكدجات للاقتراحات
    package_suggestions = list(set(
        records
        .values_list('package_name', flat=True)
        .filter(package_name__isnull=False)
        .exclude(package_name='')
    ))[:50]
    
    # ✅ إجمالي القطاعات
    total_sectors = records.values('sector').distinct().count()
    
    # ✅ إجمالي النقابات
    total_entities = entity_distribution.count()
    
    # ✅ Pagination
    paginator = Paginator(records.order_by('-admission_date'), 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'records': page_obj,
        'total_count': total_count,
        'total_amount': total_amount,
        'total_sectors': total_sectors,
        'total_entities': total_entities,
        'sector_search': sector_search,
        'specialty_search': specialty_search,
        'entity_search': entity_search,
        'sub_company_search': sub_company_search,
        'package_search': package_search,
        'date_from': date_from,
        'date_to': date_to,
        'sector_distribution': sector_distribution,
        'entity_details': entity_details,  # ✅ بيانات منظمة
        'sector_suggestions': sector_suggestions,
        'specialty_suggestions': specialty_suggestions,
        'entity_suggestions': entity_suggestions,
        'sub_company_suggestions': sub_company_suggestions,
        'package_suggestions': package_suggestions,
    }
    
    return render(request, 'frontend/sector_details.html', context)

# 🏆 أعلى الجهات                          📉 أقل الجهات

# frontend/views.py

from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.core.paginator import Paginator
from pricing_requests.models import ReportStatistic


def entities_details(request):
    """صفحة تفاصيل الجهات (آجل فقط) - أعلى وأقل"""
    
    # ✅ فلتر الجهة
    entity_search = request.GET.get("entity_search", "")
    
    # ✅ فلتر التخصص
    specialty_search = request.GET.get("specialty_search", "")
    
    # ✅ جلب السجلات (آجل فقط)
    records = ReportStatistic.objects.filter(payment_type="اجل")
    
    if entity_search:
        records = records.filter(entity_name__icontains=entity_search)
    
    if specialty_search:
        records = records.filter(specialty__icontains=specialty_search)
    
    # ✅ إحصائيات
    total_count = records.count()
    total_amount = records.aggregate(total=Sum('amount'))['total'] or 0
    
    # ✅ ✅ ✅ توزيع الجهات (أعلى وأقل)
    entity_statistics = (
        records
        .values('entity_name')
        .annotate(
            total=Count('id'),
            total_amount=Sum('amount')
        )
        .filter(entity_name__isnull=False)
        .exclude(entity_name='')
    )
    
    # ✅ أعلى الجهات
    top_entities = []
    for row in entity_statistics.order_by('-total'):
        percentage = round((row['total'] / total_count * 100), 1) if total_count > 0 else 0
        top_entities.append({
            'name': row['entity_name'],
            'total': row['total'],
            'total_amount': row['total_amount'],
            'percentage': percentage,
        })
    
    # ✅ أقل الجهات
    bottom_entities = []
    for row in entity_statistics.order_by('total', 'entity_name'):
        percentage = round((row['total'] / total_count * 100), 1) if total_count > 0 else 0
        bottom_entities.append({
            'name': row['entity_name'],
            'total': row['total'],
            'total_amount': row['total_amount'],
            'percentage': percentage,
        })
    
    # ✅ ✅ ✅ قائمة الجهات للاقتراحات (فريدة)
    entity_suggestions = list(set(
        records
        .values_list('entity_name', flat=True)
        .filter(entity_name__isnull=False)
        .exclude(entity_name='')
    ))[:50]
    
    # ✅ ✅ ✅ قائمة التخصصات للاقتراحات (فريدة)
    specialty_suggestions = list(set(
        records
        .values_list('specialty', flat=True)
        .filter(specialty__isnull=False)
        .exclude(specialty='')
    ))[:50]
    
    # ✅ إجمالي الجهات
    total_entities = records.values('entity_name').distinct().count()
    
    # ✅ Pagination (لأعلى الجهات)
    paginator_top = Paginator(top_entities, 50)
    page_number_top = request.GET.get('page_top', 1)
    top_page_obj = paginator_top.get_page(page_number_top)
    
    # ✅ Pagination (لأقل الجهات)
    paginator_bottom = Paginator(bottom_entities, 50)
    page_number_bottom = request.GET.get('page_bottom', 1)
    bottom_page_obj = paginator_bottom.get_page(page_number_bottom)
    
    context = {
        'top_entities': top_page_obj,
        'bottom_entities': bottom_page_obj,
        'total_count': total_count,
        'total_amount': total_amount,
        'total_entities': total_entities,
        'entity_search': entity_search,
        'specialty_search': specialty_search,
        'entity_suggestions': entity_suggestions,
        'specialty_suggestions': specialty_suggestions,
    }
    
    return render(request, 'frontend/entities_details.html', context)


# frontend/views.py

from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.core.paginator import Paginator
from pricing_requests.models import ReportStatistic


def sub_companies_details(request):
    """صفحة تفاصيل الشركات الفرعية (آجل فقط) - أعلى وأقل"""
    
    # ✅ فلتر الشركة الفرعية
    sub_company_search = request.GET.get("sub_company_search", "")
    
    # ✅ فلتر التخصص
    specialty_search = request.GET.get("specialty_search", "")
    
    # ✅ جلب السجلات (آجل فقط)
    records = ReportStatistic.objects.filter(payment_type="اجل")
    
    if sub_company_search:
        records = records.filter(sub_company__icontains=sub_company_search)
    
    if specialty_search:
        records = records.filter(specialty__icontains=specialty_search)
    
    # ✅ إحصائيات
    total_count = records.count()
    total_amount = records.aggregate(total=Sum('amount'))['total'] or 0
    
    # ✅ ✅ ✅ توزيع الشركات الفرعية (أعلى وأقل)
    sub_company_statistics = (
        records
        .values('sub_company')
        .annotate(
            total=Count('id'),
            total_amount=Sum('amount')
        )
        .filter(sub_company__isnull=False)
        .exclude(sub_company='')
    )
    
    # ✅ أعلى الشركات الفرعية
    top_sub_companies = []
    for row in sub_company_statistics.order_by('-total'):
        percentage = round((row['total'] / total_count * 100), 1) if total_count > 0 else 0
        top_sub_companies.append({
            'name': row['sub_company'],
            'total': row['total'],
            'total_amount': row['total_amount'],
            'percentage': percentage,
        })
    
    # ✅ أقل الشركات الفرعية
    bottom_sub_companies = []
    for row in sub_company_statistics.order_by('total', 'sub_company'):
        percentage = round((row['total'] / total_count * 100), 1) if total_count > 0 else 0
        bottom_sub_companies.append({
            'name': row['sub_company'],
            'total': row['total'],
            'total_amount': row['total_amount'],
            'percentage': percentage,
        })
    
    # ✅ ✅ ✅ قائمة الشركات الفرعية للاقتراحات (فريدة)
    sub_company_suggestions = list(set(
        records
        .values_list('sub_company', flat=True)
        .filter(sub_company__isnull=False)
        .exclude(sub_company='')
    ))[:50]
    
    # ✅ ✅ ✅ قائمة التخصصات للاقتراحات (فريدة)
    specialty_suggestions = list(set(
        records
        .values_list('specialty', flat=True)
        .filter(specialty__isnull=False)
        .exclude(specialty='')
    ))[:50]
    
    # ✅ إجمالي الشركات الفرعية
    total_sub_companies = records.values('sub_company').distinct().count()
    
    # ✅ Pagination (لأعلى الشركات)
    paginator_top = Paginator(top_sub_companies, 50)
    page_number_top = request.GET.get('page_top', 1)
    top_page_obj = paginator_top.get_page(page_number_top)
    
    # ✅ Pagination (لأقل الشركات)
    paginator_bottom = Paginator(bottom_sub_companies, 50)
    page_number_bottom = request.GET.get('page_bottom', 1)
    bottom_page_obj = paginator_bottom.get_page(page_number_bottom)
    
    context = {
        'top_sub_companies': top_page_obj,
        'bottom_sub_companies': bottom_page_obj,
        'total_count': total_count,
        'total_amount': total_amount,
        'total_sub_companies': total_sub_companies,
        'sub_company_search': sub_company_search,
        'specialty_search': specialty_search,
        'sub_company_suggestions': sub_company_suggestions,
        'specialty_suggestions': specialty_suggestions,
    }
    
    return render(request, 'frontend/sub_companies_details.html', context)

# frontend/views.py - الجزء الخاص بـ pending_analysis

def pending_analysis(request):
    """
    تحليل الحالات المعلقة من شيت 12 (ReportStatistic)
    """
    
    from django.db.models import Q, Count, Sum, Avg
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from datetime import date
    import json
    
    # ✅ جلب البيانات من ReportStatistic (شيت 12)
    pending_qs = ReportStatistic.objects.filter(payment_type="اجل")
    
    # ✅ البحث
    search = request.GET.get("search", "")
    if search:
        pending_qs = pending_qs.filter(
            Q(patient_name__icontains=search) |
            Q(entity_name__icontains=search) |
            Q(package_name__icontains=search) |
            Q(sub_company__icontains=search) |
            Q(specialty__icontains=search)
        )
    
    # ✅ الإحصائيات
    total_pending = pending_qs.count()
    total_amount = pending_qs.aggregate(total=Sum('amount'))['total'] or 0
    avg_amount = pending_qs.aggregate(avg=Avg('amount'))['avg'] or 0
    
    # ✅ عدد الجهات
    entities_count = pending_qs.values('entity_name').distinct().count()
    
    # ✅ عدد التخصصات
    specialties_count = pending_qs.exclude(specialty='').values('specialty').distinct().count()
    
    # ✅ أعلى الجهات
    top_entities = (
        pending_qs
        .values('entity_name')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    
    # ✅ أعلى التخصصات
    top_specialties = (
        pending_qs
        .exclude(specialty='')
        .values('specialty')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    
    # ✅ أعلى الباكدجات
    top_packages = (
        pending_qs
        .exclude(package_name='')
        .values('package_name')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    
    # ✅ أعلى القطاعات
    top_sectors = (
        pending_qs
        .exclude(sector='')
        .values('sector')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    
    # ✅ CHART 1: توزيع الحالات حسب الجهة (Pie)
    entity_labels = json.dumps([item['entity_name'] or 'غير محدد' for item in top_entities], ensure_ascii=False)
    entity_values = json.dumps([item['total'] for item in top_entities])
    
    # ✅ CHART 2: توزيع الحالات حسب التخصص (Bar)
    specialty_labels = json.dumps([item['specialty'] or 'غير محدد' for item in top_specialties], ensure_ascii=False)
    specialty_values = json.dumps([item['total'] for item in top_specialties])
    
    # ✅ CHART 3: عمر الطلبات (Doughnut)
    today = date.today()
    age_ranges = {
        "0-7 أيام": 0,
        "8-14 يوم": 0,
        "15-30 يوم": 0,
        "31-60 يوم": 0,
        "أكثر من 60 يوم": 0,
    }
    
    for item in pending_qs:
        if item.admission_date:
            age = (today - item.admission_date).days
            if age <= 7:
                age_ranges["0-7 أيام"] += 1
            elif age <= 14:
                age_ranges["8-14 يوم"] += 1
            elif age <= 30:
                age_ranges["15-30 يوم"] += 1
            elif age <= 60:
                age_ranges["31-60 يوم"] += 1
            else:
                age_ranges["أكثر من 60 يوم"] += 1
    
    age_labels = json.dumps(list(age_ranges.keys()), ensure_ascii=False)
    age_values = json.dumps(list(age_ranges.values()))
    
    # ✅ CHART 4: توزيع الحالات حسب القطاع (Doughnut)
    sector_labels = json.dumps([item['sector'] or 'غير محدد' for item in top_sectors], ensure_ascii=False)
    sector_values = json.dumps([item['total'] for item in top_sectors])
    
    # ✅ ألوان الـ Charts
    chart_colors = json.dumps([
        "#0d6efd", "#20c997", "#ffc107", "#dc3545", 
        "#6f42c1", "#fd7e14", "#198754", "#6610f2",
        "#0dcaf0", "#6c757d"
    ])
    
    # ✅ إضافة عمر الطلب لكل حالة
    pending_cases = list(pending_qs[:100])
    for item in pending_cases:
        if item.admission_date:
            item.age_days = (today - item.admission_date).days
        else:
            item.age_days = None
    
    # ✅ Pagination
    paginator = Paginator(pending_qs, 50)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    context = {
        # ✅ الإحصائيات
        'pending_count': f"{total_pending:,}",
        'total_cost': f"{total_amount:,.0f}",
        'avg_cost': f"{avg_amount:,.0f}",
        'entities_count': f"{entities_count:,}",
        'doctors_count': f"{specialties_count:,}",
        
        # ✅ البيانات
        'pending_cases': page_obj,
        'search': search,
        'top_entities': top_entities,
        'top_doctors': top_specialties,
        'top_specialties': top_specialties,
        'top_packages': top_packages,
        'top_sectors': top_sectors,
        'total_entities': top_entities.count(),
        'total_doctors': top_specialties.count(),
        
        # ✅ Charts Data
        'entity_chart_labels': entity_labels,
        'entity_chart_values': entity_values,
        'doctor_chart_labels': specialty_labels,
        'doctor_chart_values': specialty_values,
        'age_labels': age_labels,
        'age_values': age_values,
        'specialty_labels': sector_labels,
        'specialty_values': sector_values,
        'chart_colors': chart_colors,
    }
    
    return render(request, "frontend/pending_analysis.html", context)

def report_statistic_detail(request, pk):
    """
    صفحة تفاصيل سجل من شيت 12 (ReportStatistic)
    """
    
    record = get_object_or_404(ReportStatistic, pk=pk)
    
    # ✅ بيانات إضافية (ممكن تجيب سجلات مشابهة)
    similar_records = ReportStatistic.objects.filter(
        Q(patient_name=record.patient_name) |
        Q(entity_name=record.entity_name) |
        Q(specialty=record.specialty)
    ).exclude(pk=record.pk).order_by('-admission_date')[:10]
    
    context = {
        'record': record,
        'similar_records': similar_records,
    }
    
    return render(request, 'frontend/report_statistic_detail.html', context)
# frontend/views.py

from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Prefetch
from contracts.models import CompanyDiscountProfile, CompanyDiscount
from pricing_requests.models import CompanyDiscountRank, CompanyException, CompanyExceptionProfile, CompanyExceptionItem


# frontend/views.py

# frontend/views.py

# frontend/views.py

from django.db.models import Q, Prefetch
from django.shortcuts import render, get_object_or_404
from django.db.models import Count




def company_discounts(request):

    search = request.GET.get("search", "")
    entity_id = request.GET.get("entity")
    section = request.GET.get("section", "")
    active_tab = request.GET.get("tab", "discounts")
    
    # ============================================
    # ✅ Tab 2: مقارنة بين جهتين
    # ============================================
    compare_company_1 = request.GET.get("company1", "")
    compare_company_2 = request.GET.get("company2", "")
    compare_section = request.GET.get("compare_section", "all")
    
    selected_company = None

    if entity_id:
        selected_company = get_object_or_404(ContractEntity, pk=entity_id)
        search = selected_company.name

    # ============================================
    # ✅ جلب الشركات مع الخصومات (للتبويبات الأخرى)
    # ============================================
    companies = (
        CompanyDiscountProfile.objects
        .prefetch_related(
            Prefetch(
                "discounts",
                queryset=CompanyDiscount.objects
                    .order_by("section", "display_order")
                    .distinct(),
            )
        )
        .order_by("company_name")
        .distinct()
    )

    if search:
        companies = companies.filter(
            Q(company_name__icontains=search) |
            Q(financial_category__icontains=search)
        )

    # ============================================
    # ✅ تجميع البيانات للخصومات
    # ============================================
    company_cards = []
    seen_companies = set()

    for company in companies:
        company_key = (company.company_name, company.financial_category)
        if company_key in seen_companies:
            continue
        seen_companies.add(company_key)
        
        internal = []
        external = []
        seen_discounts = set()

        for discount in company.discounts.all():
            discount_key = (discount.section, discount.item_name)
            if discount_key in seen_discounts:
                continue
            seen_discounts.add(discount_key)
            
            if section == "internal":
                if discount.section != "داخلي":
                    continue
            elif section == "external":
                if discount.section != "خارجي":
                    continue

            if discount.details:
                discount.details_list = discount.details.split('\n') if '\n' in discount.details else [discount.details]
            else:
                discount.details_list = []

            discount.service_name = discount.item_name
            discount.discount_rate = discount.discount
            discount.items = []

            if discount.section == "داخلي":
                internal.append(discount)
            else:
                external.append(discount)

        company.internal_discounts = internal
        company.external_discounts = external
        company_cards.append(company)

    # ============================================
    # ✅ تجميع التفاصيل للخصومات
    # ============================================
    for company in company_cards:
        internal_groups = {}
        for discount in company.internal_discounts:
            key = discount.item_name
            if key not in internal_groups:
                internal_groups[key] = {
                    'service_name': discount.item_name,
                    'discount_rate': discount.discount,
                    'section': 'داخلي',
                    'items': []
                }
            if discount.details_list:
                for detail in discount.details_list:
                    if detail and detail.strip():
                        internal_groups[key]['items'].append({
                            'details': detail,
                            'net_price': discount.net_price if discount.net_price else '-'
                        })
            else:
                internal_groups[key]['items'].append({
                    'details': discount.details or '-',
                    'net_price': discount.net_price if discount.net_price else '-'
                })
        
        external_groups = {}
        for discount in company.external_discounts:
            key = discount.item_name
            if key not in external_groups:
                external_groups[key] = {
                    'service_name': discount.item_name,
                    'discount_rate': discount.discount,
                    'section': 'خارجي',
                    'items': []
                }
            if discount.details_list:
                for detail in discount.details_list:
                    if detail and detail.strip():
                        external_groups[key]['items'].append({
                            'details': detail,
                            'net_price': discount.net_price if discount.net_price else '-'
                        })
            else:
                external_groups[key]['items'].append({
                    'details': discount.details or '-',
                    'net_price': discount.net_price if discount.net_price else '-'
                })
        
        company.internal_groups = list(internal_groups.values())
        company.external_groups = list(external_groups.values())

    # ============================================
    # ✅ قائمة الشركات للـ Datalist
    # ============================================
    all_companies = (
        CompanyDiscountProfile.objects
        .values_list("company_name", flat=True)
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
                    queryset=CompanyDiscount.objects
                        .order_by("section", "display_order")
                        .distinct(),
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
                    queryset=CompanyDiscount.objects
                        .order_by("section", "display_order")
                        .distinct(),
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
    rankings = CompanyDiscountRank.objects.all()

    # ============================================
    # ✅ Tab 4: الاستثناءات (موديل قديم)
    # ============================================
    exceptions = CompanyException.objects.all()
    
          # ============================================
    # ✅ ✅ ✅ الاستثناءات (موديل جديد - CompanyExceptionProfile)
    # ============================================
    exception_profiles = (
        CompanyExceptionProfile.objects
        .prefetch_related(
            Prefetch(
                "items",
                queryset=CompanyExceptionItem.objects
                    .order_by("section", "display_order")
                    .distinct(),
            )
        )
        .order_by("entity_name")
        .distinct()
    )

    if search:
        exception_profiles = exception_profiles.filter(
            Q(entity_name__icontains=search) |
            Q(financial_category__icontains=search)
        )

    exceptions_data = []
    total_internal = 0
    total_external = 0
    total_services = 0

    for profile in exception_profiles:
        internal_items = []
        external_items = []

        # ✅ ✅ ✅ إزالة seen_items - نضيف كل العناصر بدون تكرار
        for item in profile.items.all():
            if item.section == "داخلي":
                internal_items.append(item)
                total_internal += 1
            else:
                external_items.append(item)
                total_external += 1

        total_services = total_internal + total_external

        # ✅ تجميع الخدمات الداخلية (internal_groups)
        internal_groups = {}
        for item in internal_items:
            key = item.service_name
            if key not in internal_groups:
                internal_groups[key] = {
                    'service_name': item.service_name,
                    'discount_rate': item.discount_rate,
                    'section': 'داخلي',
                    'items': []
                }
            internal_groups[key]['items'].append({
                'details': item.details or '-',
                'net_price': item.net_price if item.net_price else '-'
            })

        # ✅ تجميع الخدمات الخارجية (external_groups)
        external_groups = {}
        for item in external_items:
            key = item.service_name
            if key not in external_groups:
                external_groups[key] = {
                    'service_name': item.service_name,
                    'discount_rate': item.discount_rate,
                    'section': 'خارجي',
                    'items': []
                }
            external_groups[key]['items'].append({
                'details': item.details or '-',
                'net_price': item.net_price if item.net_price else '-'
            })

        exceptions_data.append({
            'profile': profile,
            'internal_items': internal_items,
            'external_items': external_items,
            'internal_groups': list(internal_groups.values()),
            'external_groups': list(external_groups.values()),
            'internal_count': len(internal_items),
            'external_count': len(external_items),
            'total_count': len(internal_items) + len(external_items),
        })

    

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
            # ✅ ✅ ✅ بيانات الاستثناءات مع internal_groups و external_groups
            "exceptions_data": exceptions_data,
            "exceptions_list": EXCEPTIONS_LIST,
            "total_internal": total_internal,
            "total_external": total_external,
            "total_services": total_services,
            
            # ✅ بيانات الخصومات (للتبويبات الأخرى)
            "companies": company_cards,
            "search": search,
            "selected_section": section,
            "results_count": len(company_cards),
            "selected_company": selected_company,
            "entity_id": entity_id,
            "active_tab": active_tab,

            "all_companies": all_companies,

            "company_names": all_companies,
            "compare_company_1": compare_company_1,
            "compare_company_2": compare_company_2,
            "compare_section": compare_section,
            "company_1": company_1,
            "company_2": company_2,
            "comparison_rows": comparison_rows,

            "rankings": rankings,
            "exceptions": exceptions,
        }
    )
def contract_entity_detail(request, pk):

    entity = get_object_or_404(
        ContractEntity,
        pk=pk
    )
    contract = (
        entity.contracts
        .exclude(
            financial_category__code="DEFAULT"
        )
        .select_related(
            "financial_category",
            "price_list",
        )
        .first()
    )

    if not contract:
        contract = (
            entity.contracts
            .select_related(
                "financial_category",
                "price_list",
            )
            .first()
        )

    requests = PricingRequest.objects.filter(
        entity=entity
    )

    contracts_count = entity.contracts.count()

    # ✅ أفضل طريقة لحساب عدد التسعيرات (مباشرة من قاعدة البيانات)
    contract_packages_count = (
        ContractPackage.objects
        .filter(contract__entity=entity)
        .count()
    )

    total_requests = requests.count()

    total_cost = (
        requests.aggregate(
            total=Sum("requested_cost")
        )["total"] or 0
    )

    avg_cost = (
        requests.aggregate(
            avg=Avg("requested_cost")
        )["avg"] or 0
    )

    approved = requests.filter(
        status="approved"
    ).count()

    pending = requests.filter(
        status="pending"
    ).count()

    rejected = requests.filter(
        status="rejected"
    ).count()

    service_done = requests.filter(
        status="service_done"
    ).count()

    # ✅ 1. التكلفة المستلمة ونسبة التحصيل
    total_received = (
        requests.aggregate(
            total=Sum("received_cost")
        )["total"] or 0
    )

    collection_rate = 0
    if total_cost:
        collection_rate = round(
            (total_received / total_cost) * 100,
            1
        )

    # ✅ 2. ترتيب الجهة بين جميع الجهات
    entities_rank = list(
        PricingRequest.objects
        .values("entity_id")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    entity_rank = None
    for index, item in enumerate(
        entities_rank,
        start=1
    ):
        if item["entity_id"] == entity.id:
            entity_rank = index
            break

    # ✅ 3. أعلى التخصصات
    top_specialties = (
        requests
        .values("specialty__name")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:10]
    )

    # ✅ 4. أعلى الإجراءات (حسب عدد الطلبات)
    top_procedures = (
        requests
        .exclude(
            procedure_name=""
        )
        .values("procedure_name")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:10]
    )

    # ✅ 4.1. أعلى الإجراءات تكلفة
    top_costly_procedures = (
        requests
        .exclude(
            procedure_name=""
        )
        .values(
            "procedure_name"
        )
        .annotate(
            total_cost=Sum("requested_cost"),
            total_requests=Count("id")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 5. أعلى الأطباء (مع التكلفة)
    top_doctors = (
        requests
        .exclude(
            doctor_name=""
        )
        .values("doctor_name")
        .annotate(
            total=Count("id"),
            cost=Sum("requested_cost")
        )
        .order_by("-total")[:10]
    )

    # ✅ 6. أعلى المرضى (حسب التكلفة) - موجود مسبقاً
    top_patients = (
        requests
        .values(
            "patient__full_name"
        )
        .annotate(
            total_requests=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 7. الطلبات المعلقة (الأعلى تكلفة) - موجود مسبقاً
    pending_requests = (
        requests
        .filter(
            status="pending"
        )
        .select_related(
            "patient",
            "specialty"
        )
        .order_by("-requested_cost")[:20]
    )

    # ✅ 8. أعلى المرضى تكلفة (جديد)
    top_patients_cost = (
        requests
        .values(
            "patient__full_name"
        )
        .annotate(
            total_cost=Sum("requested_cost"),
            total_requests=Count("id")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 9. أعلى المرضى عدد طلبات (جديد)
    top_patients_requests = (
        requests
        .values(
            "patient__full_name"
        )
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:10]
    )

    # ✅ 10. الحالات Pending الخاصة بالجهة (جديد)
    pending_requests_entity = (
        requests
        .filter(
            status="pending"
        )
        .select_related(
            "patient",
            "specialty"
        )
        .order_by("-id")[:20]
    )

    # ✅ 11. نسبة الموافقات (جديد)
    approved_count = requests.filter(
        status="approved"
    ).count()

    approval_rate = 0
    if total_requests:
        approval_rate = round(
            (approved_count / total_requests) * 100,
            1
        )

    latest_requests = (
        requests
        .select_related(
            "patient",
            "specialty"
        )
        .order_by("-id")[:20]
    )

    context = {
        "entity": entity,
        "selected_company": entity,
        "contract": contract,
        "contracts_count": contracts_count,
        "total_requests": total_requests,
        "total_cost": total_cost,
        "avg_cost": avg_cost,
        "contract_packages_count": contract_packages_count,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "service_done": service_done,

        # ✅ الإضافات السابقة
        "total_received": total_received,
        "collection_rate": collection_rate,
        "entity_rank": entity_rank,

        "top_specialties": top_specialties,
        "top_procedures": top_procedures,
        "top_costly_procedures": top_costly_procedures,
        "top_doctors": top_doctors,
        "top_patients": top_patients,
        "pending_requests": pending_requests,

        # ✅ الإضافات الجديدة
        "top_patients_cost": top_patients_cost,
        "top_patients_requests": top_patients_requests,
        "pending_requests_entity": pending_requests_entity,
        "approval_rate": approval_rate,

        "latest_requests": latest_requests,
    }

    return render(
        request,
        "frontend/contract_entity_detail.html",
        context
    )
    
def quality_dashboard(request):

    duplicate_entities = (
        ContractEntity.objects
        .values("name")
        .annotate(
            total=Count("id")
        )
        .filter(
            total__gt=1
        )
        .order_by("-total")
    )

    missing_specialty = (
        PricingRequest.objects.filter(
            specialty__isnull=True
        ).count()
    )

    missing_requested_cost = (
        PricingRequest.objects.filter(
            requested_cost__isnull=True
        ).count()
    )

    entities_without_contracts = (
        ContractEntity.objects.filter(
            contracts__isnull=True
        ).count()
    )

    # ✅ الطلبات بدون تكلفة (جديد)
    missing_cost_requests = (
        PricingRequest.objects
        .filter(
            requested_cost__isnull=True
        )
        .select_related(
            "patient",
            "entity",
            "specialty"
        )
        .order_by("-id")[:50]
    )

    context = {
        "duplicate_entities": duplicate_entities,
        "missing_specialty": missing_specialty,
        "missing_requested_cost": missing_requested_cost,
        "entities_without_contracts": entities_without_contracts,
        "missing_cost_requests": missing_cost_requests,  # ✅ جديد
    }

    return render(
        request,
        "frontend/quality_dashboard.html",
        context
    )
    
    


def patient_detail(request, pk):

    patient = get_object_or_404(
        Patient,
        pk=pk
    )

    requests = (
        PricingRequest.objects
        .filter(patient=patient)
        .select_related(
            "entity",
            "specialty"
        )
    )

    total_requests = requests.count()

    total_cost = (
        requests.aggregate(
            total=Sum("requested_cost")
        )["total"] or 0
    )

    total_received = (
        requests.aggregate(
            total=Sum("received_cost")
        )["total"] or 0
    )

    approved = requests.filter(
        status="approved"
    ).count()

    approval_rate = 0

    if total_requests:
        approval_rate = round(
            approved / total_requests * 100,
            1
        )

    # ✅ 1. أعلى الجهات للمريض (مع التكلفة)
    top_entities = (
        requests
        .values("entity__name")
        .annotate(
            total=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total")[:10]
    )

    # ✅ 2. أعلى الأطباء للمريض (مع التكلفة)
    top_doctors = (
        requests
        .values("doctor_name")
        .annotate(
            total=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total")[:10]
    )

    # ✅ 3. آخر الطلبات (مع العلاقات)
    latest_requests = (
        requests
        .select_related(
            "entity",
            "specialty"
        )
        .order_by("-id")[:20]
    )

    context = {
        "patient": patient,
        "total_requests": total_requests,
        "total_cost": total_cost,
        "total_received": total_received,
        "approval_rate": approval_rate,
        "top_entities": top_entities,
        "top_doctors": top_doctors,
        "latest_requests": latest_requests,
    }

    return render(
        request,
        "frontend/patient_detail.html",
        context
    )
    
    
def doctors_list(request):

    doctors = (
        PricingRequest.objects
        .exclude(doctor_name="")
        .values("doctor_name")
        .annotate(
            total_requests=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total_requests")
    )

    return render(
        request,
        "frontend/doctors_list.html",
        {
            "doctors": doctors
        }
    )
    
    
def doctor_detail(request, doctor_name):

    requests = (
        PricingRequest.objects
        .filter(
            doctor_name=doctor_name
        )
        .select_related(
            "patient",
            "entity",
            "specialty"
        )
    )

    total_requests = requests.count()

    total_cost = (
        requests.aggregate(
            total=Sum("requested_cost")
        )["total"] or 0
    )

    approved = requests.filter(
        status="approved"
    ).count()

    pending = requests.filter(
        status="pending"
    ).count()

    rejected = requests.filter(
        status="rejected"
    ).count()

    service_done = requests.filter(
        status="service_done"
    ).count()

    top_entities = (
        requests
        .values("entity__name")
        .annotate(
            total=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total")[:10]
    )

    top_patients = (
        requests
        .values("patient__full_name")
        .annotate(
            total=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total")[:10]
    )

    top_specialties = (
        requests
        .values("specialty__name")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:10]
    )

    latest_requests = (
        requests
        .order_by("-id")[:20]
    )

    context = {
        "doctor_name": doctor_name,
        "total_requests": total_requests,
        "total_cost": total_cost,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "service_done": service_done,
        "top_entities": top_entities,
        "top_patients": top_patients,
        "top_specialties": top_specialties,
        "latest_requests": latest_requests,
    }

    return render(
        request,
        "frontend/doctor_detail.html",
        context
    )
from django.utils import timezone  # ✅ أضف هذا السطر

from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.utils import timezone

def credit_package_pricing(request):
    # ============================================================
    # ✅ جلب المعاملات من الطلب
    # ============================================================
    company_id = request.GET.get("company")
    entity_id = request.GET.get("entity")
    
    if entity_id:
        company_id = entity_id
    
    package_id = request.GET.get("package")
    company_search = request.GET.get("company_search", "")
    package_search = request.GET.get("package_search", "")
    specialty_id = request.GET.get("specialty", "")
    
    selected_company = None
    
    if company_id:
        selected_company = get_object_or_404(
            ContractEntity,
            pk=company_id
        )
    
    # ============================================================
    # ✅ جلب الشركات مع Cache
    # ============================================================
    companies = cache.get('active_companies_list')
    if companies is None:
        companies = list(
            ContractEntity.objects
            .filter(
                contracts__contract_packages__is_active=True
            )
            .only("id", "name")
            .distinct()
            .order_by("name")
        )
        cache.set('active_companies_list', companies, 60 * 15)
    
    # ✅ فلترة الشركات حسب البحث
    if company_search:
        companies = [
            c for c in companies 
            if company_search.lower() in c.name.lower()
        ]
    
    # ============================================================
    # ✅ جلب التخصصات (حسب الشركة المختارة)
    # ============================================================
    specialties = []
    
    if company_id:
        # ✅ جلب التخصصات الخاصة بالشركة فقط
        cache_key = f'specialties_company_{company_id}'
        specialties = cache.get(cache_key)
        
        if specialties is None:
            # ✅ جلب الـ Package IDs النشطة للشركة
            active_package_ids = ContractPackage.objects.filter(
                contract__entity_id=company_id,
                is_active=True
            ).values_list('package_id', flat=True).distinct()
            
            # ✅ جلب التخصصات المرتبطة بهذه الـ Packages
            specialties = list(
                Specialty.objects
                .filter(
                    packages__id__in=active_package_ids
                )
                .only("id", "name")
                .distinct()
                .order_by("name")
            )
            cache.set(cache_key, specialties, 60 * 15)
    else:
        # ✅ إذا لم يتم اختيار شركة، نرجع قائمة فارغة
        specialties = []
    
    packages = []
    selected_package = None
    
    if company_id:
        # ============================================================
        # ✅ جلب الباكدجات مع Cache
        # ============================================================
        cache_key = f'packages_company_{company_id}'
        cached_packages = cache.get(cache_key)
        
        if cached_packages is not None:
            package_ids = [p['id'] for p in cached_packages]
            packages = list(
                ContractPackage.objects
                .filter(
                    id__in=package_ids,
                    is_active=True
                )
                .select_related(
                    "package",
                    "contract__entity",
                    "package__specialty"
                )
                .order_by("package__name")
            )
        else:
            # ✅ جلب من قاعدة البيانات
            packages = list(
                ContractPackage.objects
                .filter(
                    contract__entity_id=company_id,
                    is_active=True,
                )
                .select_related(
                    "package",
                    "contract__entity",
                    "package__specialty"
                )
                .order_by("package__name")
            )
            
            # ✅ تخزين في Cache
            cache_data = [
                {
                    'id': p.id,
                    'package_name': p.package.name,
                    'package_code': p.package.code,
                    'package_price': str(p.package_price),
                    'current_discount_rate': str(p.current_discount_rate) if p.current_discount_rate else None,
                    'current_discount_text': p.current_discount_text,
                    'entity_name': p.contract.entity.name,
                    'specialty_id': p.package.specialty_id if p.package else None,
                    'specialty_name': p.package.specialty.name if p.package and p.package.specialty else None,
                    'is_expired': p.valid_until < timezone.localdate() if p.valid_until else False
                }
                for p in packages
            ]
            cache.set(cache_key, cache_data, 60 * 10)
        
        # ✅ تطبيق فلتر البحث على الباكدجات
        if package_search:
            packages = [
                p for p in packages 
                if package_search.lower() in p.package.name.lower()
            ]
        
        # ✅ تطبيق فلتر التخصص
        if specialty_id:
            try:
                specialty_id = int(specialty_id)
                packages = [
                    p for p in packages
                    if p.package and p.package.specialty_id == specialty_id
                ]
            except (ValueError, TypeError):
                pass
        
        # ============================================================
        # ✅ Helper functions لتنسيق الأرقام
        # ============================================================
        def format_price(value):
            if value is None:
                return "-"
            return f"{int(float(value)):,}"
        
        def format_percentage(value):
            if value is None:
                return "-"
            if value == int(value):
                return f"{int(value)}%"
            return f"{value:.1f}%"
        
        # ✅ تنسيق الباكدجات مع إضافة التخصص
        for cp in packages:
            cp.formatted_price = format_price(cp.package_price)
            cp.formatted_discount = (
                (cp.current_discount_text or "").strip()
                or (
                    format_percentage(cp.current_discount_rate)
                    if cp.current_discount_rate
                    else "-"
                )
            )
            
            # ✅ إضافة معلومات التخصص للباكدج
            if cp.package and hasattr(cp.package, 'specialty') and cp.package.specialty:
                cp.specialty_name = cp.package.specialty.name
                cp.specialty_id = cp.package.specialty.id
            else:
                cp.specialty_name = "غير محدد"
                cp.specialty_id = None
            
            # ✅ إضافة حالة الانتهاء
            if not hasattr(cp, 'is_expired'):
                cp.is_expired = cp.valid_until < timezone.localdate() if cp.valid_until else False
    
    if package_id:
        # ✅ جلب الباكدج المحدد مع التخصص
        selected_package = get_object_or_404(
            ContractPackage.objects.select_related(
                "package",
                "contract__entity",
                "package__specialty",
            ),
            id=package_id,
            is_active=True,
        )
        
        if selected_package:
            # ============================================================
            # ✅ Helper functions
            # ============================================================
            def format_price(value):
                if value is None:
                    return "-"
                return f"{int(float(value)):,}"
            
            def format_percentage(value):
                if value is None:
                    return "-"
                if value == int(value):
                    return f"{int(value)}%"
                return f"{value:.1f}%"
            
            # ============================================================
            # ✅ تنسيق الأسعار
            # ============================================================
            selected_package.formatted_price = format_price(selected_package.package_price)
            selected_package.formatted_cash = format_price(selected_package.cash_price) if selected_package.cash_price else "-"
            selected_package.formatted_total_before = format_price(selected_package.total_before_discount) if selected_package.total_before_discount else "0"
            selected_package.formatted_special_offer = format_price(selected_package.special_offer_price) if selected_package.special_offer_price else "-"
            selected_package.formatted_current_price = format_price(selected_package.package_price)
            
            # ============================================================
            # ✅ تنسيق الخصومات
            # ============================================================
            selected_package.formatted_discount = format_percentage(selected_package.current_discount_rate) if selected_package.current_discount_rate else "0%"
            selected_package.current_discount_label = (
                (selected_package.current_discount_text or "").strip()
                or selected_package.formatted_discount
            )
            
            # ============================================================
            # ✅ السعر المقترح والخصومات المقترحة
            # ============================================================
            selected_package.formatted_suggested_price = (
                format_price(selected_package.suggested_price)
                if selected_package.suggested_price
                else "-"
            )
            
            selected_package.formatted_suggested_discount = (
                format_percentage(selected_package.suggested_discount_rate)
                if selected_package.suggested_discount_rate
                else "-"
            )
            
            # ============================================================
            # ✅ حساب التوفير وأفضل سعر
            # ============================================================
            discount_value = PricingEngine.calculate_savings(
                selected_package.package_price,
                selected_package.suggested_price
            )
            
            discount_percentage = PricingEngine.calculate_savings_percentage(
                selected_package.package_price,
                selected_package.suggested_price
            )
            
            best_price = PricingEngine.get_best_price(selected_package)
            
            selected_package.formatted_discount_value = format_price(discount_value)
            selected_package.formatted_discount_percentage = format_percentage(discount_percentage)
            selected_package.best_price = best_price
            
            # ============================================================
            # ✅ إضافة معلومات التخصص للباكدج المحدد
            # ============================================================
            if selected_package.package and hasattr(selected_package.package, 'specialty') and selected_package.package.specialty:
                selected_package.specialty_name = selected_package.package.specialty.name
                selected_package.specialty_id = selected_package.package.specialty.id
            else:
                selected_package.specialty_name = "غير محدد"
                selected_package.specialty_id = None
            
            # ============================================================
            # ✅ التحقق من انتهاء الصلاحية
            # ============================================================
            today = timezone.localdate()
            selected_package.is_expired = (
                selected_package.valid_until
                and
                selected_package.valid_until < today
            )
    
    return render(
        request,
        "frontend/credit_package_pricing.html",
        {
            "companies": companies,
            "packages": packages,
            "selected_package": selected_package,
            "selected_company": selected_company,
            "company_search": company_search,
            "package_search": package_search,
            "specialties": specialties,  # ✅ الآن التخصصات حسب الشركة
            "selected_specialty": specialty_id,
        }
    )

def cash_packages(request):

    search = request.GET.get("search", "")
    specialty = request.GET.get("specialty", "")

    packages = Package.objects.select_related(
        "specialty"
    ).filter(
        is_cash_package=True
    ).order_by("name")

    # ✅ كل الباكدجات بدون تصفية (عشان الـ Datalist)
    all_packages = Package.objects.filter(
        is_cash_package=True
    ).order_by("name")

    # البحث
    if search:
        packages = packages.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    # فلتر التخصص
    if specialty:
        packages = packages.filter(
            specialty_id=specialty
        )

    specialties = Specialty.objects.filter(
        packages__is_cash_package=True,
        is_active=True,
    ).distinct().order_by("name")

    return render(
        request,
        "frontend/cash_packages.html",
        {
            "packages": packages,
            "all_packages": all_packages,  # ✅ أضفناها هنا
            "search": search,
            "specialties": specialties,
            "selected_specialty": specialty,
        }
    )
    
    
def packages_price_list(request):
    """
    عرض الباكدجات بقائمة الأسعار (اسم الباكدج والسعر فقط)
    مع فلتر الشركة + التخصص + بحث الباكدج
    """
    company_id = request.GET.get('company')
    company_search = request.GET.get('company_search', '')
    specialty_id = request.GET.get('specialty', '')
    package_search = request.GET.get('package_search', '')
    
    packages = []
    selected_company = None
    companies = []
    specialties = []
    
    # ✅ جلب الشركات
    companies = list(
        ContractEntity.objects
        .filter(
            contracts__contract_packages__is_active=True
        )
        .only("id", "name")
        .distinct()
        .order_by("name")
    )
    
    # ✅ فلترة الشركات حسب البحث
    if company_search:
        companies = [
            c for c in companies 
            if company_search.lower() in c.name.lower()
        ]
    
    # ✅ جلب التخصصات (حسب الشركة المختارة)
    if company_id:
        selected_company = get_object_or_404(ContractEntity, id=company_id)
        
        # جلب التخصصات الخاصة بالشركة
        active_package_ids = ContractPackage.objects.filter(
            contract__entity_id=company_id,
            is_active=True
        ).values_list('package_id', flat=True).distinct()
        
        specialties = list(
            Specialty.objects
            .filter(
                packages__id__in=active_package_ids
            )
            .only("id", "name")
            .distinct()
            .order_by("name")
        )
        
        # ✅ جلب الباكدجات
        packages_query = ContractPackage.objects.filter(
            contract__entity_id=company_id,
            is_active=True
        ).select_related('package', 'contract__entity', 'package__specialty')
        
        # ✅ فلترة التخصص
        if specialty_id:
            try:
                specialty_id = int(specialty_id)
                packages_query = packages_query.filter(package__specialty_id=specialty_id)
            except (ValueError, TypeError):
                pass
        
        packages = list(packages_query.order_by('package__name'))
        
        # ✅ فلترة الباكدجات حسب البحث (في الذاكرة)
        if package_search:
            packages = [
                p for p in packages 
                if package_search.lower() in p.package.name.lower()
            ]
        
        # ✅ تنسيق الأسعار
        def format_price(value):
            if value is None:
                return "-"
            return f"{int(float(value)):,}"
        
        for cp in packages:
            cp.formatted_price = format_price(cp.package_price)
    
    return render(request, 'frontend/packages_price_list.html', {
        'companies': companies,
        'packages': packages,
        'selected_company': selected_company,
        'company_search': company_search,
        'specialties': specialties,
        'selected_specialty': specialty_id,
        'package_search': package_search,
    })
def special_offers(request):

    search = request.GET.get("search", "").strip()
    entity_id = request.GET.get("entity")
    selected_company = None
    company = request.GET.get("company", "").strip()

    if entity_id:
        selected_company = get_object_or_404(ContractEntity, pk=entity_id)
        company = selected_company.name

    offers = SpecialOffersService.get_special_offers(
        search=search,
        company=company,
    )

    companies = SpecialOffersService.get_companies()
    
    # ✅ كل أسماء الشركات للـ Datalist (كل الشركات بدون تصفية)
    all_companies = SpecialOffersService.get_companies()

    context = {
        "offers": offers,
        "companies": companies,
        "all_companies": all_companies,  # ✅ للـ Datalist
        "company": company,
        "search": search,
        "selected_company": selected_company,
        "entity_id": entity_id,
        "results_count": offers.count(),
    }

    return render(
        request,
        "frontend/special_offers.html",
        context,
    )


from django.shortcuts import render
from django.db.models import Q, Sum
from django.core.paginator import Paginator
# ... باقي الـ Imports الخاصة بك ...

from django.shortcuts import render
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
# ... باقي الـ Imports ...

# pricing_requests/views.py

def service_search(request):

    search = request.GET.get("search", "").strip()
    patient_type = request.GET.get("patient_type", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    department = request.GET.get("department", "").strip()
    insurance_company = request.GET.get("insurance_company", "").strip()

    services = (
        ServiceRecord.objects
        .all()
        .order_by("-service_date")
    )

    # ==========================================
    # Search
    # ==========================================
    if search:
        search = search.strip()
        code_match = ServiceRecord.objects.filter(service_code__iexact=search)
        if code_match.exists():
            services = services.filter(service_code__iexact=search)
        else:
            services = services.filter(
                Q(service_name__icontains=search) |
                Q(department_name__icontains=search)
            )

    # ==========================================
    # Filters
    # ==========================================
    if patient_type:
        services = services.filter(patient_type=patient_type)

    if date_from:
        services = services.filter(service_date__gte=date_from)

    if date_to:
        services = services.filter(service_date__lte=date_to)

    if department:
        services = services.filter(department_name=department)

    if insurance_company:
        services = services.filter(insurance_company=insurance_company)

    # ✅ إجمالي المبلغ (amount)
    total_amount = services.aggregate(total=Sum("amount"))["total"] or 0
    
    # ✅ ✅ إجمالي الفواتير (total_invoice) - الجديد
    total_invoice = services.aggregate(total=Sum("total_invoice"))["total"] or 0

    # ✅ جلب الفلاتر من النتائج المفلترة فقط
    departments = (
        services
        .values_list("department_name", flat=True)
        .distinct()
        .order_by("department_name")
    )

    insurance_companies = (
        services
        .values_list("insurance_company", flat=True)
        .distinct()
        .order_by("insurance_company")
    )

    # ✅ جلب اقتراحات البحث من النتائج المفلترة فقط
    service_names = (
        services
        .values_list("service_name", flat=True)
        .distinct()
        .order_by("service_name")[:100]
    )

    service_codes = (
        services
        .values_list("service_code", flat=True)
        .distinct()
        .order_by("service_code")[:100]
    )

    department_names = (
        services
        .values_list("department_name", flat=True)
        .distinct()
        .order_by("department_name")
    )

    paginator = Paginator(services, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ==========================================
    # Format Amount & Calculate Duration
    # ==========================================
    for service in page_obj:
        service.formatted_amount = (
            f"{service.amount:,.0f}"
            if service.amount is not None
            else "-"
        )
        
        # ✅ ✅ تنسيق total_invoice
        service.formatted_total_invoice = (
            f"{service.total_invoice:,.0f}"
            if service.total_invoice is not None
            else "-"
        )

        if service.stay_duration:
            service.duration_of_stay = service.stay_duration
        else:
            admission = service.admission_date
            discharge = service.discharge_date
            if admission and discharge:
                delta = discharge - admission
                service.duration_of_stay = f"{delta.days} يوم"
            else:
                service.duration_of_stay = "-"

    formatted_total_amount = f"{total_amount:,.0f}"
    formatted_total_invoice = f"{total_invoice:,.0f}"  # ✅ ✅ الجديد

    return render(
        request,
        "frontend/service_search.html",
        {
            "page_obj": page_obj,
            "results_count": services.count(),
            "total_amount": formatted_total_amount,
            "total_invoice": formatted_total_invoice,  # ✅ ✅ الجديد
            "search": search,
            "patient_type": patient_type,
            "date_from": date_from,
            "date_to": date_to,
            "department": department,
            "insurance_company": insurance_company,
            "departments": departments,
            "insurance_companies": insurance_companies,
            "service_names": service_names,
            "service_codes": service_codes,
            "department_names": department_names,
        }
    )
def pricing_details(request):

    search = request.GET.get("search", "").strip()
    group = request.GET.get("group", "").strip()
    company = request.GET.get("company", "").strip()
    doctor = request.GET.get("doctor", "").strip()
    specialty = request.GET.get("specialty", "").strip()
    accountant = request.GET.get("accountant", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    details = (
        PricingDetail.objects
        .only(
            "pricing_date",
            "patient_name",
            "company_name",
            "doctor_name",
            "procedure_name",
            "specialty_name",
            "pricing_type",
            "cost",
            "details",
            "report_name",
            "cost_notes",
            "group_name",
            "accountant_name",
            "card_number",
        )
    )

    if search:
        details = details.filter(
            Q(patient_name__icontains=search) |
            Q(procedure_name__icontains=search) |
            Q(company_name__icontains=search) |
            Q(card_number__icontains=search)
        )

    if group:
        details = details.filter(group_name=group)

    if company:
        details = details.filter(company_name=company)

    if doctor:
        details = details.filter(doctor_name=doctor)

    if specialty:
        details = details.filter(specialty_name=specialty)

    if accountant:
        details = details.filter(accountant_name=accountant)

    if date_from:
        details = details.filter(pricing_date__gte=date_from)

    if date_to:
        details = details.filter(pricing_date__lte=date_to)

    total_cost = details.aggregate(total=Sum("cost"))["total"] or 0
    average_cost = details.aggregate(avg=Avg("cost"))["avg"] or 0

    paginator = Paginator(details, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ✅ جلب الفلاتر من النتائج المفلترة
    groups = (
        details
        .exclude(group_name="")
        .values_list("group_name", flat=True)
        .distinct()
        .order_by("group_name")
    )

    companies = (
        details
        .exclude(company_name="")
        .values_list("company_name", flat=True)
        .distinct()
        .order_by("company_name")
    )

    doctors = (
        details
        .exclude(doctor_name="")
        .values_list("doctor_name", flat=True)
        .distinct()
        .order_by("doctor_name")
    )

    specialties = (
        details
        .exclude(specialty_name="")
        .values_list("specialty_name", flat=True)
        .distinct()
        .order_by("specialty_name")
    )

    accountants = (
        details
        .exclude(accountant_name="")
        .values_list("accountant_name", flat=True)
        .distinct()
        .order_by("accountant_name")
    )

    return render(
        request,
        "frontend/pricing_details.html",
        {
            "page_obj": page_obj,
            "results_count": details.count(),
            "total_cost": f"{total_cost:,.0f}",
            "average_cost": f"{average_cost:,.0f}",
            "groups": groups,
            "companies": companies,
            "doctors": doctors,
            "specialties": specialties,
            "accountants": accountants,
            "search": search,
            "group": group,
            "company": company,
            "doctor": doctor,
            "specialty": specialty,
            "accountant": accountant,
            "date_from": date_from,
            "date_to": date_to,
        }
    )
    
def similar_invoices(request):

    search = request.GET.get("search", "").strip()
    patient_name = request.GET.get("patient_name", "").strip()
    specialty = request.GET.get("specialty", "").strip()
    entity = request.GET.get("entity", "").strip()
    doctor = request.GET.get("doctor", "").strip()
    status = request.GET.get("status", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    invoices = SimilarInvoice.objects.all().order_by("-admission_date")

    # ✅ تطبيق الفلاتر
    if search:
        invoices = invoices.filter(operation_name__icontains=search)

    if patient_name:
        invoices = invoices.filter(patient_name__icontains=patient_name)

    if specialty:
        invoices = invoices.filter(specialty_name=specialty)

    if entity:
        invoices = invoices.filter(entity_name=entity)

    if doctor:
        invoices = invoices.filter(doctor_name=doctor)

    if status:
        invoices = invoices.filter(invoice_status=status)

    if date_from:
        invoices = invoices.filter(admission_date__gte=date_from)

    if date_to:
        invoices = invoices.filter(admission_date__lte=date_to)

    # ✅ الإحصائيات
    total_net_invoice = invoices.aggregate(total=Sum("net_invoice"))["total"] or 0
    total_company_share = invoices.aggregate(total=Sum("company_share"))["total"] or 0

    # ✅ Pagination
    paginator = Paginator(invoices, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ✅ تنسيق الأرقام
    for invoice in page_obj:
        invoice.formatted_net_invoice = f"{invoice.net_invoice:,.0f}" if invoice.net_invoice else "-"
        invoice.formatted_company_share = f"{invoice.company_share:,.0f}" if invoice.company_share else "-"

    # ✅ ✅ ✅ الفلاتر من النتائج (وليس من كل البيانات)
    specialties = (
        invoices
        .exclude(specialty_name="")
        .values_list("specialty_name", flat=True)
        .distinct()
        .order_by("specialty_name")
    )

    entities = (
        invoices
        .exclude(entity_name="")
        .values_list("entity_name", flat=True)
        .distinct()
        .order_by("entity_name")
    )

    doctors = (
        invoices
        .exclude(doctor_name="")
        .values_list("doctor_name", flat=True)
        .distinct()
        .order_by("doctor_name")
    )

    statuses = (
        invoices
        .exclude(invoice_status="")
        .values_list("invoice_status", flat=True)
        .distinct()
        .order_by("invoice_status")
    )

    return render(
        request,
        "frontend/similar_invoices.html",
        {
            "page_obj": page_obj,
            "results_count": invoices.count(),
            "total_net_invoice": f"{total_net_invoice:,.0f}",
            "total_company_share": f"{total_company_share:,.0f}",
            "search": search,
            "patient_name": patient_name,
            "specialty": specialty,
            "entity": entity,
            "doctor": doctor,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
            "specialties": specialties,
            "entities": entities,
            "doctors": doctors,
            "statuses": statuses,
        }
    )
    
# frontend/views.py

from django.db.models import Q
from django.shortcuts import render
from medical_catalog.models import Procedure


# frontend/views.py

def procedures(request):

    search = request.GET.get("search", "").strip()
    specialty = request.GET.get("specialty", "").strip()  # ✅ اسم التخصص (نص)
    category = request.GET.get("category", "").strip()
    show_all = request.GET.get("show_all")

    # ✅ استخدام select_related للـ Specialty
    procedures = Procedure.objects.select_related('specialty').all()

    # ==========================================
    # ✅ Search - باستخدام الحقول الصحيحة
    # ==========================================
    if search:
        procedures = procedures.filter(
            Q(name_ar__icontains=search) |      # ✅ اسم العملية بالعربي
            Q(name_en__icontains=search) |      # ✅ اسم العملية بالإنجليزي
            Q(code__icontains=search)           # ✅ الكود
        )

    # ==========================================
    # ✅ ✅ ✅ Specialty Filter - باستخدام specialty__name (النص)
    # ==========================================
    if specialty:
        procedures = procedures.filter(specialty__name=specialty)  # ✅ بدلاً من specialty_id

    # ==========================================
    # ✅ Category Filter - باستخدام classification
    # ==========================================
    if category:
        procedures = procedures.filter(classification=category)

    # ==========================================
    # ✅ التخصصات من النتائج المفلترة
    # ==========================================
    specialties = (
        procedures
        .values_list("specialty__name", flat=True)
        .distinct()
        .order_by("specialty__name")
    )

    # ==========================================
    # ✅ التصنيفات من النتائج المفلترة
    # ==========================================
    categories = (
        procedures
        .exclude(classification="")
        .values_list("classification", flat=True)
        .distinct()
        .order_by("classification")
    )

    # ==========================================
    # ✅ عدد العمليات لكل تخصص
    # ==========================================
    specialties_with_count = []
    for spec in specialties:
        count = procedures.filter(specialty__name=spec).count()
        specialties_with_count.append({
            "name": spec,
            "count": count
        })

    procedures_list = list(procedures)
    total_count = len(procedures_list)

    # ✅ لو show_all = 1، اعرض الكل، وإلا اعرض 24
    if show_all:
        display_procedures = procedures_list
    else:
        display_procedures = procedures_list[:24]

    return render(
        request,
        "frontend/procedures.html",
        {
            "procedures": display_procedures,
            "all_procedures": procedures_list if show_all else None,
            "specialties": specialties,
            "categories": categories,
            "specialties_with_count": specialties_with_count,
            "search": search,
            "specialty": specialty,  # ✅ اسم التخصص (نص)
            "category": category,
            "show_all": show_all,
            "total_count": total_count,
        }
    )
from pricing_requests.models import ProcedureFee


# pricing_requests/views.py

# frontend/views.py - procedure_fees

def procedure_fees(request):

    # ============================================
    # ✅ ✅ ✅ دالة توحيد التصنيفات في العرض
    # ============================================
    def normalize_category_for_display(category):
        """
        توحيد التصنيفات عند العرض
        """
        if not category:
            return category
        
        mapping = {
            'صغرى': 'صغـــرى',
            'كبرى': 'كــبرى',
            'طابع خاص': 'ذات طابع خاص',
            'صغرى ': 'صغـــرى',
            'كبرى ': 'كــبرى',
            'طابع خاص ': 'ذات طابع خاص',
        }
        return mapping.get(category.strip(), category.strip())

    # ============================================
    # ✅ البحث عن العملية (شيت 13) - باستخدام الحقول الصحيحة
    # ============================================
    procedure_search = request.GET.get("procedure_search", "").strip()
    
    # ============================================
    # ✅ البحث عن الجهة (شيت 14)
    # ============================================
    search = request.GET.get("search", "").strip()
    
    # ============================================
    # ✅ فلتر التصنيف - مع التوحيد
    # ============================================
    category = request.GET.get("category", "").strip()
    if category:
        category = normalize_category_for_display(category)

    # ============================================
    # ✅ العملية المختارة - باستخدام الحقول الصحيحة
    # ============================================
    selected_procedure = None
    if procedure_search:
        selected_procedure = Procedure.objects.filter(
            Q(name_ar__icontains=procedure_search) |      # ✅ name_ar
            Q(name_en__icontains=procedure_search) |      # ✅ name_en
            Q(code__icontains=procedure_search) |
            Q(classification__icontains=procedure_search) # ✅ classification
        ).first()

    # ============================================
    # ✅ الأتعاب (شيت 14)
    # ============================================
    fees = ProcedureFee.objects.all()

    # ✅ ✅ ✅ إذا تم اختيار عملية، نفلتر الأتعاب بناءً على تصنيفها
    if selected_procedure and selected_procedure.classification:  # ✅ classification
        proc_category = selected_procedure.classification
        fees = fees.filter(category=proc_category)
        category = proc_category

    # ✅ فلتر الجهة (إذا كان هناك بحث عن جهة)
    if search:
        fees = fees.filter(
            Q(entity_name__icontains=search) |
            Q(financial_category__icontains=search)
        )

    # ✅ تصفية حسب التصنيف (إذا لم يتم اختيار عملية)
    if category and not selected_procedure:
        fees = fees.filter(category=category)

    # ✅ تجميع الجهات
    entities = {}
    all_fees = fees.all()
    
    for fee in all_fees:
        key = f"{fee.entity_name}_{fee.financial_category}"
        
        if key not in entities:
            entities[key] = {
                "entity_name": fee.entity_name,
                "financial_category": fee.financial_category,
                "price_list": fee.price_list,
                "discount_rate": fee.discount_rate,
                "fees": {},
            }
        if fee.category:
            entities[key]["fees"][fee.category] = {
                "surgeon_fee": fee.surgeon_fee,
                "anesthesia_fee": fee.anesthesia_fee,
                "assistant_fee": fee.assistant_fee,
                "total_fee": fee.total_fee,
            }

    # ✅ تصحيح الـ discount_rate
    for key, entity in entities.items():
        if entity["discount_rate"] in ["0", "", None]:
            correct_fee = all_fees.filter(
                entity_name=entity["entity_name"],
                financial_category=entity["financial_category"]
            ).exclude(discount_rate__in=["0", "", None]).first()
            
            if correct_fee:
                entity["discount_rate"] = correct_fee.discount_rate

    # ✅ تجهيز القائمة
    entities_list = []
    for key, entity in entities.items():
        current_category = category if category else None
        if current_category and current_category not in entity["fees"]:
            continue
            
        entity_data = {
            "entity_name": entity["entity_name"],
            "financial_category": entity["financial_category"],
            "price_list": entity["price_list"],
            "discount_rate": entity["discount_rate"],
            "fees": entity["fees"],
        }
        if current_category and current_category in entity["fees"]:
            fee_data = entity["fees"][current_category]
            entity_data["selected_surgeon_fee"] = fee_data["surgeon_fee"]
            entity_data["selected_anesthesia_fee"] = fee_data["anesthesia_fee"]
            entity_data["selected_assistant_fee"] = fee_data["assistant_fee"]
            entity_data["selected_total_fee"] = fee_data["total_fee"]
        entities_list.append(entity_data)

    # ✅ التصنيفات للـ Dropdown - مع التوحيد
    categories = (
        ProcedureFee.objects
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )
    categories = [normalize_category_for_display(cat) for cat in categories]

    # ✅ قوائم الـ datalist
    procedures_list = Procedure.objects.all()[:100]
    
    entities_list_for_datalist = (
        ProcedureFee.objects
        .values("entity_name", "financial_category")
        .distinct()
        .order_by("entity_name")[:100]
    )

    # ✅ ✅ ✅ اختيار أول جهة تلقائياً عند البحث عن عملية
    selected_entity = None
    fees_data = None
    
    if selected_procedure and selected_procedure.classification:
        if entities_list:
            selected_entity = entities_list[0]
            fees_data = ProcedureFee.objects.filter(
                entity_name=selected_entity["entity_name"],
                financial_category=selected_entity["financial_category"],
                category=selected_procedure.classification
            ).first()

    # ✅ Debug
    print(f"🔍 Selected Procedure: {selected_procedure}")
    print(f"🔍 Classification: {selected_procedure.classification if selected_procedure else 'None'}")
    print(f"🔍 Entities List Count: {len(entities_list)}")
    print(f"🔍 Selected Entity: {selected_entity}")

    return render(
        request,
        "frontend/procedure_fees.html",
        {
            "entities": entities_list,
            "categories": categories,
            "selected_category": category,
            "search": search,
            "procedures_list": procedures_list,
            "entities_list_for_datalist": entities_list_for_datalist,
            "selected_procedure": selected_procedure,
            "selected_entity": selected_entity,
            "fees_data": fees_data,
            "procedure_search": procedure_search,
        }
    )
# frontend/views.py

from django.db.models import Q
from django.shortcuts import render
from pricing_requests.models import ExternalApproval


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def patient_search(request):
    """صفحة البحث عن مريض"""
    
    # ✅ البحث الأساسي
    search_query = request.GET.get("search", "")
    
    # ✅ الفلاتر
    attachment_type = request.GET.get("attachment_type", "")
    company_filter = request.GET.get("company", "")
    sub_account_filter = request.GET.get("sub_account", "")  # ✅ جديد
    doctor_filter = request.GET.get("doctor", "")
    specialty_filter = request.GET.get("specialty", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    
    # ✅ جلب كل السجلات
    patients = ExternalApproval.objects.all().order_by('-date', '-id')
    
    # ✅ البحث الأساسي
    if search_query:
        patients = patients.filter(
            Q(patient_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(card_number__icontains=search_query) |
            Q(medical_number__icontains=search_query) |
            Q(account_number__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(sub_account__icontains=search_query)  # ✅ إضافة البحث في الشركة الفرعية
        )
    
    # ✅ الفلاتر
    if attachment_type:
        patients = patients.filter(attachment_type__icontains=attachment_type)
    
    if company_filter:
        patients = patients.filter(company__icontains=company_filter)
    
    if sub_account_filter:  # ✅ جديد
        patients = patients.filter(sub_account__icontains=sub_account_filter)
    
    if doctor_filter:
        patients = patients.filter(doctor_name__icontains=doctor_filter)
    
    if specialty_filter:
        patients = patients.filter(specialty__icontains=specialty_filter)
    
    if date_from:
        try:
            patients = patients.filter(date__gte=date_from)
        except:
            pass
    
    if date_to:
        try:
            patients = patients.filter(date__lte=date_to)
        except:
            pass
    
    # ✅ ✅ ✅ Pagination
    paginator = Paginator(patients, 50)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # ✅ ✅ ✅ قيم الفلاتر - بناءً على الفلاتر الحالية (Dynamic)
    # ✅ نبدأ بجميع السجلات للفلاتر
    filter_queryset = ExternalApproval.objects.all()
    
    # ✅ نطبق نفس الفلاتر (ما عدا الفلتر الحالي لكل قائمة)
    if search_query:
        filter_queryset = filter_queryset.filter(
            Q(patient_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(card_number__icontains=search_query) |
            Q(medical_number__icontains=search_query) |
            Q(account_number__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(sub_account__icontains=search_query)  # ✅ إضافة البحث في الشركة الفرعية
        )
    
    # ✅ attachment_types - مع مراعاة الفلاتر التانية (ما عدا attachment_type)
    attachment_queryset = filter_queryset
    if company_filter:
        attachment_queryset = attachment_queryset.filter(company__icontains=company_filter)
    if sub_account_filter:  # ✅ جديد
        attachment_queryset = attachment_queryset.filter(sub_account__icontains=sub_account_filter)
    if doctor_filter:
        attachment_queryset = attachment_queryset.filter(doctor_name__icontains=doctor_filter)
    if specialty_filter:
        attachment_queryset = attachment_queryset.filter(specialty__icontains=specialty_filter)
    if date_from:
        attachment_queryset = attachment_queryset.filter(date__gte=date_from)
    if date_to:
        attachment_queryset = attachment_queryset.filter(date__lte=date_to)
    
    attachment_types = list(
        attachment_queryset
        .values_list('attachment_type', flat=True)
        .distinct()
        .exclude(attachment_type__isnull=True)
        .exclude(attachment_type='')
        .order_by('attachment_type')
    )
    
    # ✅ companies - مع مراعاة الفلاتر التانية (ما عدا company)
    company_queryset = filter_queryset
    if attachment_type:
        company_queryset = company_queryset.filter(attachment_type__icontains=attachment_type)
    if sub_account_filter:  # ✅ جديد
        company_queryset = company_queryset.filter(sub_account__icontains=sub_account_filter)
    if doctor_filter:
        company_queryset = company_queryset.filter(doctor_name__icontains=doctor_filter)
    if specialty_filter:
        company_queryset = company_queryset.filter(specialty__icontains=specialty_filter)
    if date_from:
        company_queryset = company_queryset.filter(date__gte=date_from)
    if date_to:
        company_queryset = company_queryset.filter(date__lte=date_to)
    
    companies = list(
        company_queryset
        .values_list('company', flat=True)
        .distinct()
        .exclude(company__isnull=True)
        .exclude(company='')
        .order_by('company')
    )
    
    # ✅ sub_accounts - مع مراعاة الفلاتر التانية (ما عدا sub_account)  # ✅ جديد
    sub_account_queryset = filter_queryset
    if attachment_type:
        sub_account_queryset = sub_account_queryset.filter(attachment_type__icontains=attachment_type)
    if company_filter:
        sub_account_queryset = sub_account_queryset.filter(company__icontains=company_filter)
    if doctor_filter:
        sub_account_queryset = sub_account_queryset.filter(doctor_name__icontains=doctor_filter)
    if specialty_filter:
        sub_account_queryset = sub_account_queryset.filter(specialty__icontains=specialty_filter)
    if date_from:
        sub_account_queryset = sub_account_queryset.filter(date__gte=date_from)
    if date_to:
        sub_account_queryset = sub_account_queryset.filter(date__lte=date_to)
    
    sub_accounts = list(
        sub_account_queryset
        .values_list('sub_account', flat=True)
        .distinct()
        .exclude(sub_account__isnull=True)
        .exclude(sub_account='')
        .order_by('sub_account')
    )
    
    # ✅ doctors - مع مراعاة الفلاتر التانية (ما عدا doctor)
    doctor_queryset = filter_queryset
    if attachment_type:
        doctor_queryset = doctor_queryset.filter(attachment_type__icontains=attachment_type)
    if company_filter:
        doctor_queryset = doctor_queryset.filter(company__icontains=company_filter)
    if sub_account_filter:  # ✅ جديد
        doctor_queryset = doctor_queryset.filter(sub_account__icontains=sub_account_filter)
    if specialty_filter:
        doctor_queryset = doctor_queryset.filter(specialty__icontains=specialty_filter)
    if date_from:
        doctor_queryset = doctor_queryset.filter(date__gte=date_from)
    if date_to:
        doctor_queryset = doctor_queryset.filter(date__lte=date_to)
    
    doctors = list(
        doctor_queryset
        .values_list('doctor_name', flat=True)
        .distinct()
        .exclude(doctor_name__isnull=True)
        .exclude(doctor_name='')
        .order_by('doctor_name')
    )
    
    # ✅ specialties - مع مراعاة الفلاتر التانية (ما عدا specialty)
    specialty_queryset = filter_queryset
    if attachment_type:
        specialty_queryset = specialty_queryset.filter(attachment_type__icontains=attachment_type)
    if company_filter:
        specialty_queryset = specialty_queryset.filter(company__icontains=company_filter)
    if sub_account_filter:  # ✅ جديد
        specialty_queryset = specialty_queryset.filter(sub_account__icontains=sub_account_filter)
    if doctor_filter:
        specialty_queryset = specialty_queryset.filter(doctor_name__icontains=doctor_filter)
    if date_from:
        specialty_queryset = specialty_queryset.filter(date__gte=date_from)
    if date_to:
        specialty_queryset = specialty_queryset.filter(date__lte=date_to)
    
    specialties = list(
        specialty_queryset
        .values_list('specialty', flat=True)
        .distinct()
        .exclude(specialty__isnull=True)
        .exclude(specialty='')
        .order_by('specialty')
    )
    
    context = {
        'search_query': search_query,
        'patients': page_obj,
        'patient_count': patients.count(),
        # ✅ الفلاتر
        'attachment_type': attachment_type,
        'company_filter': company_filter,
        'sub_account_filter': sub_account_filter,  # ✅ جديد
        'doctor_filter': doctor_filter,
        'specialty_filter': specialty_filter,
        'date_from': date_from,
        'date_to': date_to,
        # ✅ قيم الفلاتر (Dynamic)
        'attachment_types': attachment_types,
        'companies': companies,
        'sub_accounts': sub_accounts,  # ✅ جديد
        'doctors': doctors,
        'specialties': specialties,
    }
    

    
    return render(request, 'frontend/patient_search.html', context)

import re
import io
import traceback
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render

from imports.services.update_all_data_service import UpdateAllDataService


def clean_logs(text):
    """
    Remove ANSI terminal color codes from command output.
    """
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub("", text)


# ✅ متغير لتتبع التقدم
_update_progress = {
    "completed": 0,
    "current_command": "",
    "total": 16,
    "is_running": False,
    "results": [],
}


def update_progress(request):
    """API لتحديث التقدم"""
    return JsonResponse({
        "completed": _update_progress["completed"],
        "current_command": _update_progress["current_command"],
        "total": _update_progress["total"],
        "is_running": _update_progress["is_running"],
        "results": _update_progress["results"],
    })


def extract_results_from_logs(logs):
    """استخراج النتائج من الـ logs"""
    results = []
    lines = logs.split('\n')
    
    for line in lines:
        # ✅ البحث عن سطر النتيجة
        if '✅ END :' in line or '❌ END :' in line:
            is_success = '✅' in line
            # استخراج الاسم والوقت
            parts = line.split('END :')
            if len(parts) > 1:
                name_time = parts[1].strip()
                if '(' in name_time and ')' in name_time:
                    name = name_time[:name_time.rindex('(')].strip()
                    time_str = name_time[name_time.rindex('(')+1:name_time.rindex(')')]
                    results.append({
                        'name': name,
                        'time': time_str,
                        'status': 'success' if is_success else 'error'
                    })
    
    return results


def system_update(request):

    global _update_progress

    logs = None

    if request.method == "POST":

        output = io.StringIO()

        # ✅ إعادة تعيين التقدم
        _update_progress["completed"] = 0
        _update_progress["current_command"] = ""
        _update_progress["is_running"] = True
        _update_progress["results"] = []

        try:

            # ✅ تمرير الـ progress callback
            def progress_callback(command_name, completed):
                _update_progress["current_command"] = command_name
                _update_progress["completed"] = completed

            UpdateAllDataService.run(
                stdout=output,
                progress_callback=progress_callback
            )

            logs = clean_logs(output.getvalue())

            # ✅ استخراج النتائج من الـ logs
            _update_progress["results"] = extract_results_from_logs(logs)

            _update_progress["is_running"] = False
            _update_progress["completed"] = _update_progress["total"]

            messages.success(
                request,
                "تم تحديث جميع البيانات بنجاح."
            )

        except Exception as e:

            logs = clean_logs(output.getvalue())
            logs += "\n\n"
            logs += "=" * 70
            logs += "\n❌ ERROR DETAILS:\n"
            logs += traceback.format_exc()
            logs += "=" * 70

            _update_progress["is_running"] = False

            messages.error(
                request,
                f"حدث خطأ أثناء التحديث: {str(e)[:100]}"
            )

    # ✅ حساب النجاح والفشل
    success_count = sum(1 for r in _update_progress["results"] if r.get("status") == "success")
    error_count = sum(1 for r in _update_progress["results"] if r.get("status") == "error")

    # ✅ تمرير النتائج للـ HTML
    return render(
        request,
        "frontend/system_update.html",
        {
            "logs": logs,
            "results": _update_progress["results"],
            "total_commands": _update_progress["total"],
            "success_count": success_count,
            "error_count": error_count,
        }
    )