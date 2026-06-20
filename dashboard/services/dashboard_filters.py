from pricing_requests.models import PricingRequest


class DashboardFilterService:

    @staticmethod
    def apply_filters(
        queryset,
        request
    ):

        entity = request.GET.get("entity")
        status = request.GET.get("status")
        specialty = request.GET.get("specialty")
        doctor = request.GET.get("doctor")
        agent = request.GET.get("agent")
        month = request.GET.get("month")

        if entity:
            queryset = queryset.filter(
                entity__name__icontains=entity
            )

        if status:
            queryset = queryset.filter(
                status=status
            )

        if specialty:
            queryset = queryset.filter(
                specialty__name__icontains=specialty
            )

        if doctor:
            queryset = queryset.filter(
                doctor_name__icontains=doctor
            )

        if agent:
            queryset = queryset.filter(
                agent_1__full_name__icontains=agent
            )

        if month:
            queryset = queryset.filter(
                request_date__startswith=month
            )

        return queryset