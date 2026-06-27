from django.db.models.functions import TruncMonth
from contracts.services.pricing_engine import PricingEngine
from django.db.models import Count
from contracts.models import ContractPackage
from django.db.models import Count

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
    package_type = request.GET.get("type", "")  # إضافة فلتر النوع

    packages = Package.objects.select_related(
        "specialty"
    ).order_by("name")

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

    paginator = Paginator(packages, 20)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "frontend/packages.html",
        {
            "page_obj": page_obj,
            "search": search,
            "package_type": package_type,  # إرسال الفلتر إلى template
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


from contracts.models import ContractPackage
from django.db.models import Q
from django.core.paginator import Paginator


def service_search(request):

    query = request.GET.get("q", "")

    services = (
        ContractPackage.objects
        .select_related(
            "package",
            "contract__entity"
        )
        .order_by(
            "package__name"
        )
    )

    if query:
        services = services.filter(
            Q(package__name__icontains=query)
            |
            Q(package__code__icontains=query)
        )

    paginator = Paginator(
        services,
        25
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "frontend/service_search.html",
        {
            "page_obj": page_obj,
            "query": query,
        }
    )
def operations(request):
    return render(
        request,
        "frontend/operations.html"
    )



def pricing_details(request):

    search = request.GET.get("search", "")

    pricing = (
        ContractPackage.objects
        .select_related(
            "contract__entity",
            "package"
        )
        .order_by(
            "contract__entity__name"
        )
    )

    if search:
        pricing = pricing.filter(
            Q(contract__entity__name__icontains=search)
            |
            Q(package__name__icontains=search)
        )

    paginator = Paginator(pricing, 25)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)
    
    # ✅ تنسيق الأرقام بفواصل
    for item in page_obj:
        item.cash_price_formatted = f"{item.cash_price:,.0f}" if item.cash_price else "-"
        item.package_price_formatted = f"{item.package_price:,.0f}" if item.package_price else "-"

    return render(
        request,
        "frontend/pricing_details.html",
        {
            "page_obj": page_obj,
            "search": search,
        }
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

    entities = (
        ContractEntity.objects
        .annotate(
            contracts_count=Count(
                "contracts",
                distinct=True
            )
        )
        .order_by("name")
    )

    if search:
        entities = entities.filter(
            name__icontains=search
        )

    paginator = Paginator(
        entities,
        20
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    total_entities = ContractEntity.objects.count()
    total_contracts = Contract.objects.count()
    total_pricing = ContractPackage.objects.count()

    return render(
        request,
        "frontend/contract_entities.html",
        {
            "page_obj": page_obj,
            "search": search,
            "total_entities": total_entities,
            "total_contracts": total_contracts,
            "total_pricing": total_pricing,
        }
    )
    
    
    


def external_approvals(request):

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")  # إضافة فلتر الحالة

    requests_qs = (
        PricingRequest.objects
        .select_related(
            "patient",
            "entity",
            "specialty"
        )
        .order_by("-request_date")
    )

    # تطبيق البحث
    if search:
        requests_qs = requests_qs.filter(
            Q(patient__full_name__icontains=search)
            |
            Q(doctor_name__icontains=search)
            |
            Q(approval_number__icontains=search)
            |
            Q(entity__name__icontains=search)
        )

    # ⚠️ مهم: تطبيق فلتر الحالة
    if status:
        requests_qs = requests_qs.filter(status=status)

    # حساب الإحصائيات من الـ queryset المفلتر (وليس من الكل)
    total_requests = requests_qs.count()
    approval_numbers = requests_qs.exclude(
        approval_number__isnull=True
    ).exclude(
        approval_number=""
    ).count()
    approved = requests_qs.filter(status="approved").count()
    pending = requests_qs.filter(status="pending").count()
    rejected = requests_qs.filter(status="rejected").count()
    service_done = requests_qs.filter(status="service_done").count()

    # ترقيم الصفحات
    paginator = Paginator(requests_qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,  # إرسال الفلتر للـ Template

        # الإحصائيات (من الـ queryset المفلتر)
        "total_requests": total_requests,
        "approval_numbers": approval_numbers,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "service_done": service_done,
    }

    return render(
        request,
        "frontend/external_approvals.html",
        context
    )

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




def reports(request):

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

    total_requests = PricingRequest.objects.count()

    approval_numbers = (
        PricingRequest.objects
        .exclude(approval_number__isnull=True)
        .exclude(approval_number="")
        .count()
    )

    anomalies_received = (
        PricingRequest.objects.filter(
            received_cost__gt=F("requested_cost")
        ).count()
    )

    anomalies_specialty = (
        PricingRequest.objects.filter(
            specialty__name="غير محدد"
        ).count()
    )

    active_doctors = (
        PricingRequest.objects
        .exclude(doctor_name="")
        .values("doctor_name")
        .distinct()
        .count()
    )

    # ✅ توزيع حالات الطلبات
    approved = PricingRequest.objects.filter(status="approved").count()
    pending = PricingRequest.objects.filter(status="pending").count()
    rejected = PricingRequest.objects.filter(status="rejected").count()
    service_done = PricingRequest.objects.filter(status="service_done").count()
    patient_refused = PricingRequest.objects.filter(status="patient_refused").count()

    # ✅ 1. أعلى الجهات طلباً
    top_entities = (
        PricingRequest.objects
        .values("entity__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    # ✅ 2. أعلى الأطباء طلباً
    top_doctors = (
        PricingRequest.objects
        .exclude(doctor_name="")
        .values("doctor_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    # ✅ 3. أعلى الجهات تكلفة
    top_cost_entities = (
        PricingRequest.objects
        .values("entity__name")
        .annotate(
            total_cost=Sum("requested_cost")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 4. متوسط قيمة الطلب
    avg_request = (
        PricingRequest.objects.aggregate(
            avg=Avg("requested_cost")
        )["avg"] or 0
    )

    # ✅ 5. نسبة الموافقات
    approval_rate = 0
    if total_requests:
        approval_rate = (approved / total_requests) * 100

    # ✅ 6. أعلى الأطباء تكلفة
    top_doctors_cost = (
        PricingRequest.objects
        .exclude(doctor_name="")
        .values("doctor_name")
        .annotate(
            total_cost=Sum("requested_cost"),
            total_requests=Count("id")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 7. أعلى الإجراءات تكلفة
    top_procedures_cost = (
        PricingRequest.objects
        .exclude(procedure_name="")
        .values("procedure_name")
        .annotate(
            total_cost=Sum("requested_cost"),
            total_requests=Count("id")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 8. أعلى التخصصات تكلفة
    top_specialties_cost = (
        PricingRequest.objects
        .values("specialty__name")
        .annotate(
            total_cost=Sum("requested_cost"),
            total_requests=Count("id")
        )
        .order_by("-total_cost")[:10]
    )

    # ✅ 9. Chart Data - Status Doughnut
    status_chart = {
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "service_done": service_done,
        "patient_refused": patient_refused,
    }

    # ✅ 10. Chart Data - Top Entities Bar
    top_entities_chart = (
        PricingRequest.objects
        .values("entity__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    # ✅ 11. Chart Data - Top Doctors Bar
    top_doctors_chart = (
        PricingRequest.objects
        .exclude(doctor_name="")
        .values("doctor_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    # ✅ 12. Chart Data - Top Specialties Bar
    top_specialties_chart = (
        PricingRequest.objects
        .values("specialty__name")
        .annotate(
            total_requests=Count("id"),
            total_cost=Sum("requested_cost")
        )
        .order_by("-total_requests")[:10]
    )

    # ✅ 13. Chart Data - Top Cost Entities Bar
    top_cost_entities_chart = (
        PricingRequest.objects
        .values("entity__name")
        .annotate(
            total_cost=Sum("requested_cost")
        )
        .order_by("-total_cost")[:10]
    )

    context = {
        # التكاليف
        "total_requested": f"{total_requested:,.0f}",
        "total_received": f"{total_received:,.0f}",
        "difference": f"{total_requested - total_received:,.0f}",

        "total_requests": f"{total_requests:,}",
        "approval_numbers": f"{approval_numbers:,}",
        "entities": f"{ContractEntity.objects.count():,}",
        "specialties": f"{Specialty.objects.count():,}",
        "doctors": f"{active_doctors:,}",

        "received_gt_requested": f"{anomalies_received:,}",
        "missing_specialty": f"{anomalies_specialty:,}",

        # توزيع الحالات
        "approved": f"{approved:,}",
        "pending": f"{pending:,}",
        "rejected": f"{rejected:,}",
        "service_done": f"{service_done:,}",
        "patient_refused": f"{patient_refused:,}",

        # الإضافات السابقة
        "top_entities": top_entities,
        "top_doctors": top_doctors,
        "top_cost_entities": top_cost_entities,
        "avg_request": f"{avg_request:,.0f}",
        "approval_rate": round(approval_rate, 1),

        # الإضافات الجديدة
        "top_doctors_cost": top_doctors_cost,
        "top_procedures_cost": top_procedures_cost,
        "top_specialties_cost": top_specialties_cost,

        # ✅ Charts
        "status_chart": json.dumps(status_chart),

        # ✅ Bar Chart Data - Entities
        "top_entities_labels": json.dumps([
            x["entity__name"] for x in top_entities_chart
        ]),
        "top_entities_values": json.dumps([
            x["total"] for x in top_entities_chart
        ]),

        # ✅ Bar Chart Data - Doctors
        "top_doctors_labels": json.dumps([
            x["doctor_name"] for x in top_doctors_chart
        ]),
        "top_doctors_values": json.dumps([
            x["total"] for x in top_doctors_chart
        ]),

        # ✅ Bar Chart Data - Specialties
        "top_specialties_labels": json.dumps([
            x["specialty__name"] or "غير محدد" for x in top_specialties_chart
        ]),
        "top_specialties_values": json.dumps([
            x["total_requests"] for x in top_specialties_chart
        ]),

        # ✅ Bar Chart Data - Cost Entities (مع تحويل Decimal إلى float)
        "top_cost_entities_labels": json.dumps([
            x["entity__name"] for x in top_cost_entities_chart
        ]),
        "top_cost_entities_values": json.dumps([
            float(x["total_cost"]) for x in top_cost_entities_chart  # ✅ تحويل Decimal إلى float
        ]),
    }

    return render(
        request,
        "frontend/reports.html",
        context
    )
def pending_analysis(request):

    pending_qs = (
        PricingRequest.objects
        .filter(status="pending")
        .select_related(
            "patient",
            "entity",
            "specialty"
        )
        .order_by("-request_date")
    )

    search = request.GET.get("search", "")

    if search:
        pending_qs = pending_qs.filter(
            Q(patient__full_name__icontains=search) |
            Q(doctor_name__icontains=search) |
            Q(entity__name__icontains=search)
        )

    top_entities = (
        PricingRequest.objects
        .filter(status="pending")
        .values("entity__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    top_doctors = (
        PricingRequest.objects
        .filter(status="pending")
        .values("doctor_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    # ✅ عدد الجهات والأطباء في الحالات المعلقة
    entities_count = pending_qs.values('entity').distinct().count()
    doctors_count = pending_qs.exclude(doctor_name="").values('doctor_name').distinct().count()

    # ✅ إضافة عمر الطلب لكل حالة
    today = date.today()
    pending_cases = list(pending_qs[:100])
    for item in pending_cases:
        if item.request_date:
            item.age_days = (today - item.request_date).days
        else:
            item.age_days = None

    # ✅ تنسيق الأرقام بفواصل
    avg_cost = pending_qs.aggregate(avg=Avg("requested_cost"))["avg"] or 0

    context = {
        "pending_count": f"{pending_qs.count():,}",
        "avg_cost": f"{avg_cost:,.0f}",
        "top_entities": top_entities,
        "top_doctors": top_doctors,
        "pending_cases": pending_cases,
        "entities_count": f"{entities_count:,}",
        "doctors_count": f"{doctors_count:,}",
    }

    return render(
        request,
        "frontend/pending_analysis.html",
        context
    )
def company_discounts(request):

    avg_discount = (
        ContractPackage.objects
        .exclude(current_discount_rate__isnull=True)
        .aggregate(avg=Avg("current_discount_rate"))
    )["avg"] or 0

    top_discounts = (
        ContractPackage.objects
        .values("contract__entity__name")
        .annotate(
            avg_discount=Avg("current_discount_rate")
        )
        .exclude(avg_discount__isnull=True)
        .order_by("-avg_discount")[:20]
    )

    low_discounts = (
        ContractPackage.objects
        .values("contract__entity__name")
        .annotate(
            avg_discount=Avg("current_discount_rate")
        )
        .exclude(avg_discount__isnull=True)
        .order_by("avg_discount")[:20]
    )

    context = {
        "avg_discount": avg_discount,
        "top_discounts": top_discounts,
        "low_discounts": low_discounts,
    }

    return render(
        request,
        "frontend/company_discounts.html",
        context
    )
    
    
    
from pricing_requests.models import PricingRequest
from django.db.models import Q

def similar_invoices(request):

    search = request.GET.get("search", "")

    invoices = PricingRequest.objects.none()

    if search:

        invoices = (
            PricingRequest.objects
            .select_related(
                "patient",
                "entity",
                "specialty"
            )
            .filter(
                Q(procedure_name__icontains=search)
                |
                Q(doctor_name__icontains=search)
                |
                Q(entity__name__icontains=search)
            )
            .order_by("-request_date")
        )

    # ✅ تنسيق الأرقام بفواصل
    for item in invoices:
        item.requested_cost_formatted = f"{item.requested_cost:,.0f}" if item.requested_cost else "-"
        item.received_cost_formatted = f"{item.received_cost:,.0f}" if item.received_cost else "-"

    return render(
        request,
        "frontend/similar_invoices.html",
        {
            "search": search,
            "invoices": invoices,
        }
    )
    



def contract_entity_detail(request, pk):

    entity = get_object_or_404(
        ContractEntity,
        pk=pk
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

def credit_package_pricing(request):

    company_id = request.GET.get("company")
    package_id = request.GET.get("package")
    company_search = request.GET.get("company_search", "")
    package_search = request.GET.get("package_search", "")

    # ✅ جلب الشركات مع فلتر البحث
    companies = (
    ContractEntity.objects
    .filter(
        contracts__contract_packages__is_active=True
    )
    .distinct()
    .order_by("name")
)

    # ✅ تطبيق فلتر البحث على الشركات
    if company_search:
        companies = companies.filter(name__icontains=company_search)

    packages = ContractPackage.objects.none()
    selected_package = None

    if company_id:

        packages = (
            ContractPackage.objects
            .filter(
                contract__entity_id=company_id,
                is_active=True,
            )
            .select_related("package")
            .order_by("package__name")
        )

        # ✅ تطبيق فلتر البحث على الباكدجات
        if package_search:
            packages = packages.filter(package__name__icontains=package_search)

    if package_id:

        # ✅ إضافة is_active=True في get_object_or_404
        selected_package = get_object_or_404(
            ContractPackage.objects.select_related(
                "package",
                "contract__entity",
                "package__specialty",
            ),
            id=package_id,
            is_active=True,
        )

        # ✅ تنسيق الأرقام
        if selected_package:
            # ============================================================
            # ✅ Helper function لتنسيق الأرقام بدون أصفار زائدة
            # ============================================================
            def format_price(value):
                if value is None:
                    return "-"
                # لو الرقم صحيح (زي 12950.00)
                if value == int(value):
                    return f"{int(value):,}"
                # لو في كسور (زي 12950.50)
                return f"{value:,.2f}"

            def format_percentage(value):
                if value is None:
                    return "-"
                # لو النسبة صحيحة (زي 5.00)
                if value == int(value):
                    return f"{int(value)}%"
                # لو في كسور (زي 5.50)
                return f"{value:.1f}%"

            # ============================================================
            # ✅ تنسيق الأسعار (بدون أصفار زائدة)
            # ============================================================
            selected_package.formatted_price = format_price(selected_package.package_price)
            selected_package.formatted_cash = format_price(selected_package.cash_price) if selected_package.cash_price else "-"
            selected_package.formatted_total_before = format_price(selected_package.total_before_discount) if selected_package.total_before_discount else "0"
            selected_package.formatted_special_offer = format_price(selected_package.special_offer_price) if selected_package.special_offer_price else "-"
            selected_package.formatted_current_price = format_price(selected_package.package_price)

            # ============================================================
            # ✅ تنسيق الخصومات (بدون أصفار زائدة)
            # ============================================================
            selected_package.formatted_discount = format_percentage(selected_package.current_discount_rate) if selected_package.current_discount_rate else "0%"
            
            # ============================================================
# ✅ النص المعروض للخصم الحالي
# ============================================================

            if (
                selected_package.current_discount_text
                and
                selected_package.current_discount_text != "nan"
            ):
                selected_package.current_discount_label = (
                    selected_package.current_discount_text
                )
            else:
                selected_package.current_discount_label = (
                    selected_package.formatted_discount
                )
                
            
            

            # ============================================================
            # ✅ السعر المقترح
            # ============================================================
            selected_package.formatted_suggested_price = (
                format_price(selected_package.suggested_price)
                if selected_package.suggested_price
                else "-"
            )

            # ============================================================
            # ✅ نسبة الخصم المقترحة
            # ============================================================
            selected_package.formatted_suggested_discount = (
                format_percentage(selected_package.suggested_discount_rate)
                if selected_package.suggested_discount_rate
                else "-"
            )

            # ============================================================
            # ✅ قيمة التخفيض
            # ============================================================
            discount_value = PricingEngine.calculate_savings(
                selected_package.package_price,
                selected_package.suggested_price
            )

            discount_percentage = (
                PricingEngine.calculate_savings_percentage(
                    selected_package.package_price,
                    selected_package.suggested_price
                )
            )

            best_price = PricingEngine.get_best_price(
                selected_package
            )

            selected_package.formatted_discount_value = format_price(discount_value)
            selected_package.formatted_discount_percentage = format_percentage(discount_percentage)

            selected_package.best_price = best_price

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
            "selected_company": company_id,
            "company_search": company_search,
            "package_search": package_search,
        }
    )