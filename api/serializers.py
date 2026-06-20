from rest_framework import serializers
from pricing_requests.models import (
    Patient,
    PricingRequest,
    PricingRequestFile,
    PricingRequestNote,
)
from medical_catalog.models import (
    Specialty,
    Procedure,
)

from contracts.models import (
    ContractEntity,
    SubCompany,
    FinancialCategory,
    PriceList,
    Contract,
    ContractPackage
)


class SpecialtySerializer(serializers.ModelSerializer):

    class Meta:
        model = Specialty
        fields = [
            "id",
            "name",
            "color",
            "icon",
        ]


class ProcedureSerializer(serializers.ModelSerializer):

    specialty_name = serializers.CharField(
        source="specialty.name",
        read_only=True
    )

    class Meta:
        model = Procedure
        fields = [
            "id",
            "code",
            "name_ar",
            "name_en",
            "classification",
            "specialty",
            "specialty_name",
        ]


class ContractEntitySerializer(serializers.ModelSerializer):

    class Meta:
        model = ContractEntity
        fields = [
            "id",
            "name",
            "contract_type",
        ]


class SubCompanySerializer(serializers.ModelSerializer):

    entity_name = serializers.CharField(
        source="entity.name",
        read_only=True
    )

    class Meta:
        model = SubCompany
        fields = [
            "id",
            "name",
            "code",
            "entity",
            "entity_name",
        ]
        
        
class FinancialCategorySerializer(serializers.ModelSerializer):

    entity_name = serializers.CharField(
        source="entity.name",
        read_only=True
    )

    class Meta:
        model = FinancialCategory
        fields = [
            "id",
            "code",
            "description",
            "entity",
            "entity_name",
        ]
        
class PriceListSerializer(serializers.ModelSerializer):

    class Meta:
        model = PriceList
        fields = [
            "id",
            "name",
            "effective_from",
        ]
        
class ContractSerializer(serializers.ModelSerializer):

    entity_name = serializers.CharField(
        source="entity.name",
        read_only=True
    )

    financial_category_code = serializers.CharField(
        source="financial_category.code",
        read_only=True
    )

    price_list_name = serializers.CharField(
        source="price_list.name",
        read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id",

            "entity",
            "entity_name",

            "financial_category",
            "financial_category_code",

            "price_list",
            "price_list_name",

            "contract_type",
            "medical_service_discount",
            "effective_from",
            "notes",
        ]
        
class ContractPackageSerializer(serializers.ModelSerializer):

    contract_name = serializers.CharField(
        source="contract.entity.name",
        read_only=True
    )

    package_name = serializers.CharField(
        source="package.name",
        read_only=True
    )

    class Meta:
        model = ContractPackage
        fields = [
            "id",

            "contract",
            "contract_name",

            "package",
            "package_name",

            "package_price",
            "total_before_discount",
            "current_discount_rate",

            "cash_price",
            "special_offer_price",

            "effective_from",
            "notes",
        ]
        
class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "card_number",
            "phone",
            "medical_number",
            "notes",
        ]
        
class PricingRequestSerializer(serializers.ModelSerializer):

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
    
    sub_company_name = serializers.CharField(
    source="sub_company.name",
    read_only=True
    )

    agent_1_name = serializers.CharField(
        source="agent_1.full_name",
        read_only=True
    )

    agent_2_name = serializers.CharField(
        source="agent_2.full_name",
        read_only=True
    )

    class Meta:
        model = PricingRequest

        fields = [
            "id",

            "patient",
            "patient_name",

            "entity",
            "entity_name",

            "sub_company",
            "sub_company_name",  # 👈 لازم تضيفه هنا


            "doctor_name",

            "specialty",
            "specialty_name",

            "procedure_name",

            "requested_cost",
            "received_cost",

            "approval_number",
            "approval_date",
            "approval_expiry_date",

            "account_number",

            "request_date",
            "expected_admission_date",
            "service_date",

            "status",
            "main_status",
            "billing_status",

            "agent_1",
            "agent_1_name",
            "agent_2",
             "agent_2_name",  # 👈 لازم ده
        ]
        
        
class PricingRequestFileSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PricingRequestFile

        fields = [
            "id",
            "pricing_request",
            "file_type",
            "file",
            "uploaded_at",
        ]
        
class PricingRequestNoteSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PricingRequestNote

        fields = [
            "id",
            "pricing_request",
            "department",
            "note",
            "created_by",
            "created_at",
        ]