# frontend/urls.py

from django.urls import path,re_path
from . import views

urlpatterns = [
    path("dashboard/", views.home, name="home"),
    path(
        "packages/",
        views.packages,
        name="packages"
    ),
    path(
    "reports/packages/",
    views.report_packages,
    name="report_packages",
    ),
    path(
    "cash-packages/",
    views.cash_packages,
    name="cash_packages"
    ),
    path('packages-price-list/', views.packages_price_list, name='packages_price_list'),  # ✅ أضف هذا السطر

    
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
    
    path('api/update-progress/', views.update_progress, name='update_progress'),  # ✅ أضف هذا
    path('api/progress-stream/', views.progress_stream, name='progress_stream'),  # ✅ جديد

    
    path(
    'api/cancel-update/',
    views.cancel_update,
    name='cancel_update'
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
    path('external-approvals/<str:filter_type>/', views.external_approvals_detail, name='external_approvals_detail'),


    path('patient-search/', views.patient_search, name='patient_search'),

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
    path('reports/payment-details/', views.payment_details, name='payment_details'),


    path('reports/sector-details/', views.sector_details, name='sector_details'),

    path('reports/entities-details/', views.entities_details, name='entities_details'),
    path('reports/sub-companies-details/', views.sub_companies_details, name='sub_companies_details'),

    path(
    "pending-analysis/",
    views.pending_analysis,
    name="pending_analysis"
),
    path('report-statistic/<int:pk>/', views.report_statistic_detail, name='report_statistic_detail'),
    

    
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
    
    path('doctors/', views.doctors_list, name='doctors_list'),

    path('doctor/<str:doctor_name>/', views.doctor_detail, name='doctor_detail'),
    path('package-comparison/', views.package_performance_comparison, name='package_comparison'),


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


path(
    "system/update/",
    views.system_update,
    name="system_update",
),
path('api/clear-logs/', views.clear_logs, name='clear_logs'),

path(
    "ajax/package-filters/",
    views.get_package_filters,
    name="package_filters",
),
    re_path(r'^doctor/(?P<doctor_name>.+)/status/(?P<status_type>[^/]+)/$', views.doctor_status_detail, name='doctor_status_detail'),

]