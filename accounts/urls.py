from django.urls import path
from . import views


urlpatterns = [
    # Landing Page / Login
    path(
        "",
        views.login_view,
        name="login",
    ),

    # Login URL
    path(
        "login/",
        views.login_view,
        name="login_page",
    ),

    # Logout
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]