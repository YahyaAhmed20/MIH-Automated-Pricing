from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def login_view(request):
    # إذا كان المستخدم مسجل دخول بالفعل، لا نعيده إلى صفحة Login
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None and user.is_active:
            login(request, user)

            # بعد نجاح الدخول نرجع للصفحة الرئيسية الحالية
            return redirect("home")

        # Authentication فشل
        return render(
            request,
            "accounts/login.html",
            {
                "login_error": True,
            },
        )

    return render(
        request,
        "accounts/login.html",
    )


def logout_view(request):
    logout(request)
    return redirect("login")
