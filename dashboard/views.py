from datetime import datetime, timedelta
from datetime import datetime, timedelta
from django.db.models import Count, F, Q, Sum, Avg, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from openpyxl import Workbook

from accounts.models import User
from contracts.models import Contract
from medical_catalog.models import Package, Specialty
from pricing_requests.models import (
    PricingRequest,
    Patient,
    PricingRequestNote,
)
from .serializers import (
    DashboardRequestSerializer,
    PricingRequestDetailsSerializer,
)


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_filtered_queryset(request, base_qs=None):
    """
    Apply date range filters (start, end) to a queryset.

    Usage:
        qs = get_filtered_queryset(request)
        qs = get_filtered_queryset(request, SomeModel.objects.filter(...))
    """
    if base_qs is None:
        qs = PricingRequest.objects.all()
    else:
        qs = base_qs

    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    if start_date:
        qs = qs.filter(request_date__gte=start_date)

    if end_date:
        qs = qs.filter(request_date__lte=end_date)

    return qs


# ------------------------------------------------------------------------------
# Pagination
# ------------------------------------------------------------------------------

class DashboardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ------------------------------------------------------------------------------
# Core Stats
# ------------------------------------------------------------------------------

class DashboardStatsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = {
            "patients": Patient.objects.count(),
            "pricing_requests": qs.count(),
            "contracts": Contract.objects.count(),
            "packages": Package.objects.count(),
            "notes": PricingRequestNote.objects.count(),

            "approved_requests": qs.filter(
                status="approved"
            ).count(),

            "pending_requests": qs.filter(
                status="pending"
            ).count(),

            "rejected_requests": qs.filter(
                status="rejected"
            ).count(),

            "service_done_requests": qs.filter(
                status="service_done"
            ).count(),

            "patient_refused_requests": qs.filter(
                status="patient_refused"
            ).count(),
        }

        return Response(data)


class DashboardStatusChartAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response(data)


class DashboardSpecialtyChartAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values(specialty_name=F("specialty__name"))
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response(data)


class DashboardEntityChartAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values(entity_name=F("entity__name"))
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response(data)


class DashboardMonthlyChartAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .exclude(request_date__isnull=True)
            .annotate(month=TruncMonth("request_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        result = []

        for item in data:
            result.append({
                "month": item["month"].strftime("%Y-%m"),
                "count": item["count"]
            })

        return Response(result)


class DashboardLatestRequestsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        qs = (
            qs
            .select_related("patient", "entity", "specialty")
            .order_by("-id")[:20]
        )

        serializer = DashboardRequestSerializer(qs, many=True)

        return Response(serializer.data)


class DashboardPendingRequestsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        qs = (
            qs
            .filter(status="pending")
            .select_related("patient", "entity", "specialty")
            .order_by("-request_date")
        )

        serializer = DashboardRequestSerializer(qs, many=True)

        return Response(serializer.data)


class DashboardSearchAPIView(APIView):

    def get(self, request):

        query = request.GET.get("q", "").strip()

        qs = get_filtered_queryset(request)

        qs = qs.select_related("patient", "entity", "specialty")

        if query:
            qs = qs.filter(
                Q(patient__full_name__icontains=query)
                |
                Q(patient__card_number__icontains=query)
                |
                Q(patient__medical_number__icontains=query)
                |
                Q(approval_number__icontains=query)
                |
                Q(entity__name__icontains=query)
                |
                Q(procedure_name__icontains=query)
                |
                Q(doctor_name__icontains=query)
            )

        serializer = DashboardRequestSerializer(
            qs.order_by("-id").distinct()[:50],
            many=True
        )

        return Response(serializer.data)


class DashboardTopProceduresAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values("procedure_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )

        return Response(data)


class DashboardTopDoctorsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values("doctor_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )

        return Response(data)


class DashboardApprovalRateAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        approved = qs.filter(status="approved").count()
        rejected = qs.filter(status="rejected").count()
        pending = qs.filter(status="pending").count()

        total = approved + rejected

        approval_rate = round(
            (approved / total) * 100, 2
        ) if total > 0 else 0

        return Response({
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "approval_rate": approval_rate,
        })


class DashboardFinancialAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        total_requested = (
            qs.aggregate(total=Sum("requested_cost"))["total"] or 0
        )

        total_received = (
            qs.aggregate(total=Sum("received_cost"))["total"] or 0
        )

        avg_requested = (
            qs.aggregate(avg=Avg("requested_cost"))["avg"] or 0
        )

        avg_received = (
            qs.aggregate(avg=Avg("received_cost"))["avg"] or 0
        )

        difference = total_requested - total_received

        requests_with_received_cost = qs.filter(
            received_cost__isnull=False
        ).count()

        total_requests = qs.count()

        received_coverage_rate = round(
            requests_with_received_cost * 100 / total_requests,
            2
        ) if total_requests else 0

        return Response({
            "total_requested": total_requested,
            "total_received": total_received,
            "difference": difference,
            "average_requested": round(float(avg_requested), 2),
            "average_received": round(float(avg_received), 2),
            "requests_with_received_cost": requests_with_received_cost,
            "received_coverage_rate": received_coverage_rate,
        })


class PricingRequestDetailsAPIView(RetrieveAPIView):

    queryset = (
        PricingRequest.objects
        .select_related("patient", "entity", "specialty")
        .prefetch_related("notes")
    )

    serializer_class = PricingRequestDetailsSerializer


class DashboardTopAgentsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = []

        for user in User.objects.all():

            agent1_count = qs.filter(agent_1=user).count()
            agent2_count = qs.filter(agent_2=user).count()

            total = agent1_count + agent2_count

            if total > 0:
                data.append({
                    "agent": user.full_name,
                    "count": total,
                    "agent_1_count": agent1_count,
                    "agent_2_count": agent2_count,
                })

        data = sorted(
            data,
            key=lambda x: x["count"],
            reverse=True
        )

        return Response(data[:20])


class DashboardApprovalSummaryAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        total_requests = qs.count()

        approval_numbers = (
            qs
            .exclude(approval_number__isnull=True)
            .exclude(approval_number="")
            .count()
        )

        approved = qs.filter(status="approved").count()
        pending = qs.filter(status="pending").count()
        rejected = qs.filter(status="rejected").count()
        service_done = qs.filter(status="service_done").count()
        patient_refused = qs.filter(status="patient_refused").count()

        approval_issued_rate = round(
            approval_numbers * 100 / total_requests, 2
        ) if total_requests else 0

        current_approval_rate = round(
            approved * 100 / (approved + rejected), 2
        ) if (approved + rejected) else 0

        service_done_rate = round(
            service_done * 100 / total_requests, 2
        ) if total_requests else 0

        rejection_rate = round(
            rejected * 100 / total_requests, 2
        ) if total_requests else 0

        return Response({
            "total_requests": total_requests,
            "approval_numbers": approval_numbers,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
            "service_done": service_done,
            "patient_refused": patient_refused,
            "approval_issued_rate": approval_issued_rate,
            "current_approval_rate": current_approval_rate,
            "service_done_rate": service_done_rate,
            "rejection_rate": rejection_rate,
        })


class DashboardRequestsAPIView(ListAPIView):

    serializer_class = DashboardRequestSerializer
    pagination_class = DashboardPagination

    def get_queryset(self):

        qs = (
            PricingRequest.objects
            .select_related(
                "patient",
                "entity",
                "specialty",
                "agent_1",
                "agent_2",
            )
        )

        qs = get_filtered_queryset(self.request, qs)

        status = self.request.GET.get("status")
        entity = self.request.GET.get("entity")
        specialty = self.request.GET.get("specialty")
        doctor = self.request.GET.get("doctor")
        agent = self.request.GET.get("agent")
        search = self.request.GET.get("search")
        from_date = self.request.GET.get("from_date")
        to_date = self.request.GET.get("to_date")
        ordering = self.request.GET.get("ordering")

        if status:
            qs = qs.filter(status=status)

        if entity:
            qs = qs.filter(entity__name__icontains=entity)

        if specialty:
            qs = qs.filter(specialty__name__icontains=specialty)

        if doctor:
            qs = qs.filter(doctor_name__icontains=doctor)

        if agent:
            qs = qs.filter(
                Q(agent_1__full_name__icontains=agent)
                |
                Q(agent_2__full_name__icontains=agent)
            )

        if from_date:
            qs = qs.filter(request_date__gte=from_date)

        if to_date:
            qs = qs.filter(request_date__lte=to_date)

        if search:
            qs = qs.filter(
                Q(patient__full_name__icontains=search)
                |
                Q(patient__medical_number__icontains=search)
                |
                Q(patient__card_number__icontains=search)
                |
                Q(doctor_name__icontains=search)
                |
                Q(procedure_name__icontains=search)
                |
                Q(approval_number__icontains=search)
                |
                Q(entity__name__icontains=search)
            )

        allowed_ordering = [
            "request_date",
            "-request_date",
            "requested_cost",
            "-requested_cost",
            "id",
            "-id",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-id")

        return qs


class DashboardFiltersAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        statuses = list(
            qs
            .values_list("status", flat=True)
            .distinct()
            .order_by("status")
        )

        entities = list(
            qs
            .values_list("entity__name", flat=True)
            .distinct()
            .exclude(entity__name__isnull=True)
            .exclude(entity__name="")
            .order_by("entity__name")
        )

        specialties = list(
            qs
            .values_list("specialty__name", flat=True)
            .distinct()
            .exclude(specialty__name__isnull=True)
            .exclude(specialty__name="")
            .order_by("specialty__name")
        )

        doctors = list(
            qs
            .values_list("doctor_name", flat=True)
            .distinct()
            .exclude(doctor_name__isnull=True)
            .exclude(doctor_name="")
            .order_by("doctor_name")
        )

        agents = list(
            User.objects
            .values_list("full_name", flat=True)
            .exclude(full_name__isnull=True)
            .exclude(full_name="")
            .order_by("full_name")
        )

        return Response({
            "statuses": statuses,
            "entities": entities,
            "specialties": specialties,
            "doctors": doctors,
            "agents": agents,
        })


class DashboardExportAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        qs = qs.select_related(
            "patient",
            "entity",
            "specialty",
            "agent_1",
            "agent_2",
        )

        status = request.GET.get("status")
        entity = request.GET.get("entity")
        specialty = request.GET.get("specialty")
        doctor = request.GET.get("doctor")
        agent = request.GET.get("agent")
        search = request.GET.get("search")

        if status:
            qs = qs.filter(status=status)

        if entity:
            qs = qs.filter(entity__name__icontains=entity)

        if specialty:
            qs = qs.filter(specialty__name__icontains=specialty)

        if doctor:
            qs = qs.filter(doctor_name__icontains=doctor)

        if agent:
            qs = qs.filter(
                Q(agent_1__full_name__icontains=agent)
                |
                Q(agent_2__full_name__icontains=agent)
            )

        if search:
            qs = qs.filter(
                Q(patient__full_name__icontains=search)
                |
                Q(patient__medical_number__icontains=search)
                |
                Q(patient__card_number__icontains=search)
                |
                Q(doctor_name__icontains=search)
                |
                Q(procedure_name__icontains=search)
                |
                Q(approval_number__icontains=search)
                |
                Q(entity__name__icontains=search)
            )

        wb = Workbook()
        ws = wb.active
        ws.title = "Pricing Requests"

        ws.append([
            "Patient",
            "Medical Number",
            "Entity",
            "Specialty",
            "Doctor",
            "Procedure",
            "Status",
            "Approval Number",
            "Requested Cost",
            "Received Cost",
            "Request Date",
        ])

        for obj in qs:
            ws.append([
                obj.patient.full_name,
                obj.patient.medical_number,
                obj.entity.name if obj.entity else "",
                obj.specialty.name if obj.specialty else "",
                obj.doctor_name,
                obj.procedure_name,
                obj.status,
                obj.approval_number,
                obj.requested_cost,
                obj.received_cost,
                obj.request_date,
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="pricing_requests.xlsx"'

        wb.save(response)

        return response


class DashboardAdvancedStatsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        total_requests = qs.count()

        approval_requests = (
            qs
            .exclude(approval_number__isnull=True)
            .exclude(approval_number="")
            .count()
        )

        highest_requested = (
            qs.aggregate(value=Max("requested_cost"))["value"] or 0
        )

        highest_received = (
            qs.aggregate(value=Max("received_cost"))["value"] or 0
        )

        avg_requested = (
            qs.aggregate(value=Avg("requested_cost"))["value"] or 0
        )

        avg_received = (
            qs.aggregate(value=Avg("received_cost"))["value"] or 0
        )

        active_entities = (
            qs
            .values("entity")
            .distinct()
            .count()
        )

        active_specialties = (
            qs
            .values("specialty")
            .distinct()
            .count()
        )

        active_doctors = (
            qs
            .exclude(doctor_name="")
            .values("doctor_name")
            .distinct()
            .count()
        )

        return Response({
            "total_requests": total_requests,
            "requests_with_approval": approval_requests,
            "requests_without_approval": total_requests - approval_requests,
            "approval_coverage_rate": round(
                approval_requests * 100 / total_requests, 2
            ) if total_requests else 0,
            "highest_requested_cost": highest_requested,
            "highest_received_cost": highest_received,
            "avg_requested_cost": round(float(avg_requested), 2),
            "avg_received_cost": round(float(avg_received), 2),
            "active_entities": active_entities,
            "active_specialties": active_specialties,
            "active_doctors": active_doctors,
        })


class DashboardDoctorPerformanceAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values("doctor_name")
            .annotate(
                total_requests=Count("id"),
                approved=Count("id", filter=Q(status="approved")),
                rejected=Count("id", filter=Q(status="rejected")),
                service_done=Count("id", filter=Q(status="service_done")),
            )
            .exclude(doctor_name="")
            .order_by("-total_requests")[:20]
        )

        results = []

        for item in data:
            decision_total = item["approved"] + item["rejected"]

            approval_rate = round(
                item["approved"] * 100 / decision_total, 2
            ) if decision_total else 0

            results.append({
                "doctor": item["doctor_name"],
                "total_requests": item["total_requests"],
                "approved": item["approved"],
                "rejected": item["rejected"],
                "service_done": item["service_done"],
                "approval_rate": approval_rate,
            })

        return Response(results)


class DashboardEntityPerformanceAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values("entity__name")
            .annotate(
                total_requests=Count("id"),
                approved=Count("id", filter=Q(status="approved")),
                rejected=Count("id", filter=Q(status="rejected")),
                service_done=Count("id", filter=Q(status="service_done")),
                total_requested=Sum("requested_cost"),
                total_received=Sum("received_cost"),
            )
            .exclude(entity__isnull=True)
            .order_by("-total_requests")
        )

        results = []

        for item in data:
            decision_total = item["approved"] + item["rejected"]

            approval_rate = round(
                item["approved"] * 100 / decision_total, 2
            ) if decision_total else 0

            results.append({
                "entity": item["entity__name"],
                "total_requests": item["total_requests"],
                "approved": item["approved"],
                "rejected": item["rejected"],
                "service_done": item["service_done"],
                "total_requested": item["total_requested"] or 0,
                "total_received": item["total_received"] or 0,
                "approval_rate": approval_rate,
            })

        return Response(results)


class DashboardMonthlyFinancialsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .exclude(request_date__isnull=True)
            .annotate(month=TruncMonth("request_date"))
            .values("month")
            .annotate(
                total_requested=Sum("requested_cost"),
                total_received=Sum("received_cost"),
                total_requests=Count("id"),
            )
            .order_by("month")
        )

        results = []

        for item in data:
            requested = item["total_requested"] or 0
            received = item["total_received"] or 0

            results.append({
                "month": item["month"].strftime("%Y-%m"),
                "total_requests": item["total_requests"],
                "total_requested": requested,
                "total_received": received,
                "difference": requested - received,
            })

        return Response(results)


class DashboardEntityRankingAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .values("entity__name")
            .annotate(
                total_requests=Count("id"),
                total_requested=Sum("requested_cost"),
                total_received=Sum("received_cost"),
                approved=Count("id", filter=Q(status="approved")),
                rejected=Count("id", filter=Q(status="rejected")),
            )
            .exclude(entity__isnull=True)
            .order_by("-total_requested")
        )

        results = []

        for item in data:
            requested = item["total_requested"] or 0
            received = item["total_received"] or 0

            approval_total = item["approved"] + item["rejected"]

            approval_rate = round(
                item["approved"] * 100 / approval_total, 2
            ) if approval_total else 0

            results.append({
                "entity": item["entity__name"],
                "total_requests": item["total_requests"],
                "total_requested": requested,
                "total_received": received,
                "difference": requested - received,
                "approval_rate": approval_rate,
            })

        return Response(results)


class DashboardAnomaliesAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        received_gt_requested = qs.filter(
            received_cost__gt=F("requested_cost")
        ).count()

        missing_doctor = qs.filter(
            doctor_name=""
        ).count()

        missing_specialty = qs.filter(
            specialty__name="غير محدد"
        ).count()

        high_cost_requests = qs.filter(
            requested_cost__gte=100000
        ).count()

        approvals_with_rejection = (
            qs
            .exclude(approval_number__isnull=True)
            .exclude(approval_number="")
            .filter(status="rejected")
            .count()
        )

        return Response({
            "received_gt_requested": received_gt_requested,
            "missing_doctor": missing_doctor,
            "missing_specialty": missing_specialty,
            "high_cost_requests": high_cost_requests,
            "approvals_with_rejection": approvals_with_rejection,
        })


class DashboardExpiringApprovalsAPIView(APIView):

    def get(self, request):

        today = timezone.now().date()

        qs = (
            PricingRequest.objects
            .filter(approval_expiry_date__isnull=False)
            .filter(approval_expiry_date__gte=today)
            .filter(approval_expiry_date__lte=today + timedelta(days=14))
            .select_related("patient", "entity")
            .order_by("approval_expiry_date")
        )

        data = []

        for obj in qs:
            days_left = (obj.approval_expiry_date - today).days

            data.append({
                "id": obj.id,
                "patient": obj.patient.full_name,
                "entity": obj.entity.name,
                "approval_number": obj.approval_number,
                "expiry_date": obj.approval_expiry_date,
                "days_left": days_left,
            })

        return Response(data)


class DashboardHomeAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        total_requests = qs.count()

        approved = qs.filter(status="approved").count()
        pending = qs.filter(status="pending").count()
        rejected = qs.filter(status="rejected").count()
        service_done = qs.filter(status="service_done").count()
        patient_refused = qs.filter(status="patient_refused").count()

        total_requested = (
            qs.aggregate(total=Sum("requested_cost"))["total"] or 0
        )

        total_received = (
            qs.aggregate(total=Sum("received_cost"))["total"] or 0
        )

        approval_numbers = (
            qs
            .exclude(approval_number__isnull=True)
            .exclude(approval_number="")
            .count()
        )

        latest_requests = (
            qs
            .select_related("patient", "entity", "specialty")
            .order_by("-id")[:10]
        )

        latest_requests_data = (
            DashboardRequestSerializer(
                latest_requests,
                many=True
            ).data
        )

        return Response({
            "stats": {
                "patients": Patient.objects.count(),
                "pricing_requests": total_requests,
                "contracts": Contract.objects.count(),
                "packages": Package.objects.count(),
                "notes": PricingRequestNote.objects.count(),
            },
            "status_summary": {
                "approved": approved,
                "pending": pending,
                "rejected": rejected,
                "service_done": service_done,
                "patient_refused": patient_refused,
            },
            "financial": {
                "total_requested": total_requested,
                "total_received": total_received,
                "difference": total_requested - total_received,
            },
            "approval": {
                "approval_numbers": approval_numbers,
                "approval_coverage_rate": round(
                    approval_numbers * 100 / total_requests, 2
                ) if total_requests else 0,
            },
            "latest_requests": latest_requests_data,
        })


class DashboardAlertsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        alerts = []

        pending_count = qs.filter(status="pending").count()

        if pending_count:
            alerts.append({
                "type": "warning",
                "title": "طلبات Pending",
                "value": pending_count,
            })

        rejected_count = qs.filter(status="rejected").count()

        if rejected_count:
            alerts.append({
                "type": "danger",
                "title": "طلبات مرفوضة",
                "value": rejected_count,
            })

        approval_count = (
            qs
            .exclude(approval_number__isnull=True)
            .exclude(approval_number="")
            .count()
        )

        alerts.append({
            "type": "info",
            "title": "موافقات صادرة",
            "value": approval_count,
        })

        high_cost_requests = qs.filter(
            requested_cost__gte=100000
        ).count()

        if high_cost_requests:
            alerts.append({
                "type": "danger",
                "title": "طلبات مرتفعة التكلفة",
                "value": high_cost_requests,
            })

        return Response({"alerts": alerts})


class DashboardTrendsAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        data = (
            qs
            .exclude(request_date__isnull=True)
            .annotate(month=TruncMonth("request_date"))
            .values("month")
            .annotate(
                requests=Count("id"),
                requested_cost=Sum("requested_cost"),
                received_cost=Sum("received_cost"),
            )
            .order_by("month")
        )

        results = []

        for item in data:
            results.append({
                "month": item["month"].strftime("%Y-%m"),
                "requests": item["requests"],
                "requested_cost": item["requested_cost"] or 0,
                "received_cost": item["received_cost"] or 0,
            })

        return Response(results)


class DashboardExecutiveSummaryAPIView(APIView):

    def get(self, request):

        qs = get_filtered_queryset(request)

        total_requests = qs.count()

        approved = qs.filter(status="approved").count()
        rejected = qs.filter(status="rejected").count()
        pending = qs.filter(status="pending").count()
        service_done = qs.filter(status="service_done").count()

        total_requested = (
            qs.aggregate(total=Sum("requested_cost"))["total"] or 0
        )

        total_received = (
            qs.aggregate(total=Sum("received_cost"))["total"] or 0
        )

        approval_numbers = (
            qs
            .exclude(approval_number__isnull=True)
            .exclude(approval_number="")
            .count()
        )

        top_entity = (
            qs
            .values("entity__name")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )

        top_doctor = (
            qs
            .values("doctor_name")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )

        top_agent = (
            User.objects
            .annotate(total=Count("agent1_requests"))
            .order_by("-total")
            .first()
        )

        anomalies = {
            "received_gt_requested": qs.filter(
                received_cost__gt=F("requested_cost")
            ).count(),
            "missing_specialty": qs.filter(
                specialty__name="غير محدد"
            ).count(),
            "approvals_with_rejection": (
                qs
                .exclude(approval_number__isnull=True)
                .exclude(approval_number="")
                .filter(status="rejected")
                .count()
            ),
            "high_cost_requests": qs.filter(
                requested_cost__gte=100000
            ).count(),
        }

        return Response({
            "summary": {
                "total_requests": total_requests,
                "approved": approved,
                "rejected": rejected,
                "pending": pending,
                "service_done": service_done,
            },
            "financial": {
                "total_requested": total_requested,
                "total_received": total_received,
                "difference": total_requested - total_received,
            },
            "approvals": {
                "approval_numbers": approval_numbers,
            },
            "leaders": {
                "top_entity": top_entity,
                "top_doctor": top_doctor,
                "top_agent": top_agent.full_name if top_agent else None,
            },
            "anomalies": anomalies,
        })
        


class DashboardKPIComparisonAPIView(APIView):

    def get(self, request):

        start = request.GET.get("start")
        end = request.GET.get("end")

        if not start or not end:
            return Response({
                "error": "start and end are required"
            }, status=400)

        start_date = datetime.strptime(
            start,
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            end,
            "%Y-%m-%d"
        ).date()

        days = (end_date - start_date).days + 1

        previous_end = start_date - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)

        current_qs = PricingRequest.objects.filter(
            request_date__gte=start_date,
            request_date__lte=end_date,
        )

        previous_qs = PricingRequest.objects.filter(
            request_date__gte=previous_start,
            request_date__lte=previous_end,
        )

        current_requests = current_qs.count()
        previous_requests = previous_qs.count()

        current_cost = (
            current_qs.aggregate(
                total=Sum("requested_cost")
            )["total"] or 0
        )

        previous_cost = (
            previous_qs.aggregate(
                total=Sum("requested_cost")
            )["total"] or 0
        )

        requests_growth = round(
            (
                (current_requests - previous_requests)
                / previous_requests
            ) * 100,
            2
        ) if previous_requests else 0

        cost_growth = round(
            (
                (current_cost - previous_cost)
                / previous_cost
            ) * 100,
            2
        ) if previous_cost else 0

        return Response({
            "current_period": {
                "start": start,
                "end": end,
                "requests": current_requests,
                "requested_cost": current_cost,
            },
            "previous_period": {
                "start": previous_start,
                "end": previous_end,
                "requests": previous_requests,
                "requested_cost": previous_cost,
            },
            "growth": {
                "requests_growth": requests_growth,
                "cost_growth": cost_growth,
            }
        })