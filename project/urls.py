
"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # ==========================
    # Authentication
    # ==========================

    path(
        "",
        include("accounts.urls")
    ),

    # ==========================
    # Main Frontend Application
    # ==========================

    path(
        "",
        include("frontend.urls")
    ),

    # ==========================
    # Django Admin
    # ==========================

    path(
        "admin/",
        admin.site.urls
    ),

    # ==========================
    # APIs
    # ==========================

    path(
        "api/",
        include("api.urls")
    ),

    path(
        "api/dashboard/",
        include("dashboard.urls")
    ),
]


# ==========================
# Static / Media - Development
# ==========================

if settings.DEBUG:

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
