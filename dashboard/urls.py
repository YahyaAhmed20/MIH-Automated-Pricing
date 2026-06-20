

from django.urls import path
from .views import (
    DashboardAlertsAPIView,
    DashboardAnomaliesAPIView,
    DashboardApprovalSummaryAPIView,
    DashboardDoctorPerformanceAPIView,
    DashboardEntityPerformanceAPIView,
    DashboardEntityRankingAPIView,
    DashboardExecutiveSummaryAPIView,
    DashboardExpiringApprovalsAPIView,
    DashboardExportAPIView,
    DashboardFinancialAPIView,
    DashboardHomeAPIView,
    DashboardKPIComparisonAPIView,
    DashboardPendingRequestsAPIView,
    DashboardRequestsAPIView,
    DashboardStatsAPIView,
    DashboardStatusChartAPIView,
    DashboardSpecialtyChartAPIView,
    DashboardEntityChartAPIView,
    DashboardMonthlyChartAPIView,
    DashboardTopAgentsAPIView,
    DashboardTopDoctorsAPIView,
    DashboardTopProceduresAPIView,
    DashboardApprovalRateAPIView,
    DashboardTrendsAPIView,
    PricingRequestDetailsAPIView,
    DashboardFiltersAPIView,    
    DashboardAdvancedStatsAPIView,
    DashboardMonthlyFinancialsAPIView
)





from .views import (
    DashboardLatestRequestsAPIView,
    DashboardSearchAPIView
)
from .views import DashboardStatsAPIView

urlpatterns = [
    
    
    path(
    "home/",
    DashboardHomeAPIView.as_view()
),
    path(
        "stats/",
        DashboardStatsAPIView.as_view(),
        name="dashboard-stats",
    ),
    
    path(
    "status-chart/",
    DashboardStatusChartAPIView.as_view(),
    name="dashboard-status-chart",
),
    
    path(
    "specialty-chart/",
    DashboardSpecialtyChartAPIView.as_view(),
    name="dashboard-specialty-chart",
),
    path(
    "entity-chart/",
    DashboardEntityChartAPIView.as_view(),
    name="dashboard-entity-chart",
),
    
    path(
    "monthly-chart/",
    DashboardMonthlyChartAPIView.as_view(),
    name="dashboard-monthly-chart",
),
    path(
    "latest-requests/",
    DashboardLatestRequestsAPIView.as_view(),
    name="dashboard-latest-requests",
),
    
    path(
    "pending-requests/",
    DashboardPendingRequestsAPIView.as_view(),
    name="dashboard-pending-requests",
),
    
    path(
    "search/",
    DashboardSearchAPIView.as_view(),
    name="dashboard-search",
),
    
    
    path(
    "top-procedures/",
    DashboardTopProceduresAPIView.as_view(),
    name="dashboard-top-procedures",
),
    
    path(
    "top-doctors/",
    DashboardTopDoctorsAPIView.as_view(),
    name="dashboard-top-doctors",
),
    
    path(
    "approval-rate/",
    DashboardApprovalRateAPIView.as_view(),
    name="dashboard-approval-rate",
),
    
    
    path(
    "financial/",
    DashboardFinancialAPIView.as_view(),
    name="dashboard-financial",
),
    
    
    path(
    "requests/<int:pk>/",
    PricingRequestDetailsAPIView.as_view(),
    name="dashboard-request-details",
),
    
    path(
    "top-agents/",
    DashboardTopAgentsAPIView.as_view(),
),
    path(
    "approval-summary/",
    DashboardApprovalSummaryAPIView.as_view(),
    name="dashboard-approval-summary",
),
    path(
    "requests/",
    DashboardRequestsAPIView.as_view(),
),
    path(
    "filters/",
    DashboardFiltersAPIView.as_view(),
),
    
    path(
    "export/",
    DashboardExportAPIView.as_view(),
    name="dashboard-export",
),
    path(
    "advanced-stats/",
    DashboardAdvancedStatsAPIView.as_view(),
    name="advanced-stats",
),
    
    path(
    "entity-performance/",
    DashboardEntityPerformanceAPIView.as_view()
),

path(
    "doctor-performance/",
    DashboardDoctorPerformanceAPIView.as_view()
),

path(
    "expiring-approvals/",
    DashboardExpiringApprovalsAPIView.as_view()
),
path(
    "alerts/",
    DashboardAlertsAPIView.as_view()
),

path(
    "doctor-performance/",
    DashboardDoctorPerformanceAPIView.as_view()
),

path(
    "entity-performance/",
    DashboardEntityPerformanceAPIView.as_view()
),

path(
    "monthly-financials/",
    DashboardMonthlyFinancialsAPIView.as_view()
),
path(
    "entity-ranking/",
    DashboardEntityRankingAPIView.as_view()
),

path(
    "anomalies/",
    DashboardAnomaliesAPIView.as_view()
),

path(
    "executive-summary/",
    DashboardExecutiveSummaryAPIView.as_view()
),

path(
    "trends/",
    DashboardTrendsAPIView.as_view()
),

path(
    "kpi-comparison/",
    DashboardKPIComparisonAPIView.as_view()
),
    
]