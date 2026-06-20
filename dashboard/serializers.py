from rest_framework import serializers

from rest_framework import serializers
from pricing_requests.models import (
    PricingRequest,
    PricingRequestNote
)
from pricing_requests.models import (
    PricingRequest
)


class DashboardRequestSerializer(
    serializers.ModelSerializer
):

    patient_name = serializers.CharField(
        source="patient.full_name",
        read_only=True
    )

    entity_name = serializers.CharField(
        source="entity.name",
        read_only=True
    )

    specialty_name = serializers.CharField(
        source="specialty.name",
        read_only=True
    )

    class Meta:

        model = PricingRequest

        fields = [
            "id",

            "patient_name",

            "entity_name",

            "specialty_name",

            "procedure_name",

            "status",

            "request_date",

            "approval_number",
        ]
        
        
class PricingRequestNoteSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PricingRequestNote

        fields = [
            "id",
            "department",
            "note",
            "created_at",
        ]


class PricingRequestDetailsSerializer(
    serializers.ModelSerializer
):

    patient_name = serializers.CharField(
        source="patient.full_name"
    )

    medical_number = serializers.CharField(
        source="patient.medical_number"
    )

    entity_name = serializers.CharField(
        source="entity.name"
    )

    specialty_name = serializers.CharField(
        source="specialty.name"
    )

    notes = PricingRequestNoteSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = PricingRequest

        fields = [
            "id",

            "patient_name",
            "medical_number",

            "entity_name",
            "specialty_name",

            "doctor_name",
            "procedure_name",

            "requested_cost",
            "received_cost",

            "status",
            "main_status",
            "billing_status",

            "approval_number",
            "approval_date",
            "approval_expiry_date",

            "request_date",
            "expected_admission_date",
            "service_date",

            "notes",
        ]