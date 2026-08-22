from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.http import url_has_allowed_host_and_scheme


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

            # ===== Remember Me =====
            remember_me = request.POST.get("remember_me")

            if remember_me:
                # 30 يوم
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                # تنتهي عند إغلاق المتصفح
                request.session.set_expiry(0)

            # ===== Redirect to requested page =====
            next_url = request.POST.get("next") or request.GET.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

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


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")