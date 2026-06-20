from django.urls import path
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    SpecialtyViewSet,
    ProcedureViewSet,
    ContractEntityViewSet,
    SubCompanyViewSet,
    FinancialCategoryViewSet,
    PriceListViewSet,
    ContractViewSet,
    ContractPackageViewSet,
    PackagePricingAPIView,
    PatientViewSet,
    PricingRequestViewSet,
    PricingRequestFileViewSet,
    PricingRequestNoteViewSet,
)

router = DefaultRouter()

router.register(
    "specialties",
    SpecialtyViewSet,
    basename="specialties"
)

router.register(
    "procedures",
    ProcedureViewSet,
    basename="procedures"
)

router.register(
    "entities",
    ContractEntityViewSet,
    basename="entities"
)

router.register(
    "sub-companies",
    SubCompanyViewSet,
    basename="sub-companies"
)
    
router.register(
    "financial-categories",
    FinancialCategoryViewSet,
    basename="financial-categories"
)

router.register(
    "price-lists",
    PriceListViewSet,
    basename="price-lists"
)

router.register(
    "contracts",
    ContractViewSet,
    basename="contracts"
)
router.register(
    "contract-packages",
    ContractPackageViewSet,
    basename="contract-packages"
)

router.register(
    "patients",
    PatientViewSet,
    basename="patients"
)

router.register(
    "pricing-requests",
    PricingRequestViewSet,
    basename="pricing-requests"
)

router.register(
    "pricing-request-files",
    PricingRequestFileViewSet,
    basename="pricing-request-files"
)

router.register(
    "pricing-request-notes",
    PricingRequestNoteViewSet,
    basename="pricing-request-notes"
)

urlpatterns = [
    path(
        "token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),
    path(
    "package-pricing/",
    PackagePricingAPIView.as_view(),
    name="package-pricing"
),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
]

urlpatterns += router.urls