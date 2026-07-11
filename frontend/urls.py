# frontend/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path(
        "packages/",
        views.packages,
        name="packages"
    ),
    path(
    "cash-packages/",
    views.cash_packages,
    name="cash_packages"
    ),
    
    path('packages/create/', views.package_create, name='package_create'),

    path(
        "contracts/",
        views.contracts,
        name="contracts"
    ),

    path(
        "discounts/",
        views.discounts,
        name="discounts"
    ),

    path(
        "offers/",
        views.offers,
        name="offers"
    ),

    path(
        "service-search/",
        views.service_search,
        name="service_search",
    ),
    
    path(
        "external-approvals/",
        views.external_approvals,
        name="external_approvals"
    ),

    path(
        "external-approvals/<int:pk>/",
        views.approval_detail,
        name="approval_detail"
    ),

    path(
        "operations/",
        views.operations,
        name="operations"
    ),

    path(
        "pricing-details/",
        views.pricing_details,
        name="pricing_details",
    ),
    path(
    "contract-entities/",
    views.contract_entities,
    name="contract_entities",
    ),
    

    path(
        "reports/",
        views.reports_statistics,
        name="reports"
    ),

    path(
        "approvals/",
        views.approvals,
        name="approvals"
    ),
    

   

    path(
        "price-lists/",
        views.price_lists,
        name="price_lists"
    ),
    
    path('reports/specialty/<str:specialty_name>/', views.specialty_detail, name='specialty_detail'),  # ✅ جديد

  
    
    path(
    "pending-analysis/",
    views.pending_analysis,
    name="pending_analysis"
),
    
    path(
    "company-discounts/",
    views.company_discounts,
    name="company_discounts",
    ),
    
    path(
    "special-offers/",
    views.special_offers,
    name="special_offers",
    ),
    
    path(
        "procedures/",
        views.procedures,
        name="procedures",
    ),
    path(
        "similar-invoices/",
        views.similar_invoices,
        name="similar_invoices",
    ),
    
    path(
        "procedure-fees/",
        views.procedure_fees,
        name="procedure_fees"
    ),
    
    path(
    "contract-entities/<int:pk>/",
    views.contract_entity_detail,
    name="contract_entity_detail"
),
    path(
    "quality-dashboard/",
    views.quality_dashboard,
    name="quality_dashboard"
),
    
    path(
    "patients/<int:pk>/",
    views.patient_detail,
    name="patient_detail"
),
    
    path(
    "doctors/",
    views.doctors_list,
    name="doctors_list"
),

path(
    "doctors/<path:doctor_name>/",
    views.doctor_detail,
    name="doctor_detail"
),

path(
    "credit-package-pricing/",
    views.credit_package_pricing,
    name="credit_package_pricing"
),
]