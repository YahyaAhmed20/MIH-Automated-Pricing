from pricing_requests.models import (
    Patient,
    PricingRequest,
    PricingRequestFile,
    PricingRequestNote,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pricing_engine.services import PricingCalculator
from pricing_engine.exceptions import (
    ContractPackageNotFoundError
)

from rest_framework import viewsets

from medical_catalog.models import (
    Specialty,
    Procedure,
)



from .serializers import (
    SpecialtySerializer,
    ProcedureSerializer,
    ContractEntitySerializer,
    SubCompanySerializer,
    FinancialCategorySerializer,
    PriceListSerializer,
    ContractSerializer,
    ContractPackageSerializer,
    PatientSerializer,
    PricingRequestSerializer,
    PricingRequestFileSerializer,
    PricingRequestNoteSerializer,
)
from contracts.models import (
    ContractEntity,
    SubCompany,
    FinancialCategory,
    PriceList,
    Contract,
    ContractPackage,
)


class SpecialtyViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Specialty.objects.filter(
        is_active=True
    )

    serializer_class = SpecialtySerializer

    search_fields = [
        "name"
    ]

    ordering_fields = [
        "name"
    ]


class ProcedureViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Procedure.objects.filter(
    is_active=True
    ).select_related(
    "specialty"
)

    serializer_class = ProcedureSerializer

    filterset_fields = [
        "specialty"
    ]

    search_fields = [
        "name_ar",
        "code",
    ]

    ordering_fields = [
        "name_ar",
        "code",
    ]


class ContractEntityViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ContractEntity.objects.filter(
        is_active=True
    )


    serializer_class = ContractEntitySerializer

    search_fields = [
        "name"
    ]

    ordering_fields = [
        "name"
    ]


class SubCompanyViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = SubCompany.objects.filter(
        is_active=True
    ).select_related(
        "entity"
    )

    serializer_class = SubCompanySerializer

    filterset_fields = [
        "entity"
    ]

    search_fields = [
        "name",
        "code",
    ]

    ordering_fields = [
        "name"
    ]
    
class FinancialCategoryViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = FinancialCategory.objects.filter(
        is_active=True
    ).select_related(
        "entity"
    )

    serializer_class = FinancialCategorySerializer

    filterset_fields = [
        "entity"
    ]

    search_fields = [
        "code",
        "description",
    ]

    ordering_fields = [
        "code",
    ]
    
class PriceListViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = PriceList.objects.filter(
        is_active=True
    )

    serializer_class = PriceListSerializer

    search_fields = [
        "name"
    ]

    ordering_fields = [
        "name",
        "effective_from",
    ]
    
    
class ContractViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Contract.objects.select_related(
        "entity",
        "financial_category",
        "price_list",
    )

    serializer_class = ContractSerializer

    filterset_fields = [
        "entity",
        "financial_category",
        "price_list",
    ]

    ordering_fields = [
        "effective_from",
    ]
    
class ContractPackageViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ContractPackage.objects.select_related(
        "contract",
        "contract__entity",
        "package",
    )

    serializer_class = ContractPackageSerializer

    filterset_fields = [
        "contract",
        "package",
    ]

    ordering_fields = [
        "package_price",
        "effective_from",
    ]
    
    
class PackagePricingAPIView(APIView):

    def get(self, request):

        contract_id = request.query_params.get(
            "contract_id"
        )

        package_id = request.query_params.get(
            "package_id"
        )

        discount_percentage = request.query_params.get(
            "discount_percentage"
        )

        try:

            data = (
                PricingCalculator.calculate_final_price(
                    contract_id=contract_id,
                    package_id=package_id,
                    discount_percentage=discount_percentage,
                )
            )

            return Response(data)

        except ContractPackageNotFoundError as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
class PatientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Patient.objects.all()

    serializer_class = PatientSerializer

    search_fields = [
        "full_name",
        "phone",
        "medical_number",
        "card_number",
    ]

    ordering_fields = [
        "full_name",
    ]
    
    
class PricingRequestViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = PricingRequest.objects.select_related(
        "patient",
        "entity",
        "sub_company",
        "specialty",
        "agent_1",
        "agent_2",
        "created_by",
)

    serializer_class = PricingRequestSerializer

    filterset_fields = [
        "status",
        "entity",
        "specialty",
    ]

    search_fields = [
        "patient__full_name",
        "patient__phone",
        "patient__medical_number",
        "patient__card_number",
        "procedure_name",
    ]

    ordering_fields = [
        "created_at",
        "expected_admission_date",
    ]
    
    


class PricingRequestFileViewSet(
    viewsets.ReadOnlyModelViewSet
):

    queryset = PricingRequestFile.objects.select_related(
        "pricing_request"
    )

    serializer_class = PricingRequestFileSerializer

    filterset_fields = [
        "pricing_request",
        "file_type",
    ]
    


class PricingRequestNoteViewSet(
    viewsets.ReadOnlyModelViewSet
):

    queryset = PricingRequestNote.objects.select_related(
        "pricing_request",
        "created_by",
    )

    serializer_class = PricingRequestNoteSerializer

    filterset_fields = [
        "pricing_request",
        "department",
    ]