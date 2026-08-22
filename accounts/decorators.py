from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

from .authorization import Authorization


def login_required(view_func):
    """
    Require authenticated user.

    Anonymous users are redirected to the login page.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                login_url="/login/",
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required(permission):
    """
    Require a single permission.

    Anonymous users → Login
    Authenticated users without permission → 403
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Authentication
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url="/login/",
                )

            # Authorization
            authz = Authorization(request.user)

            if not authz.can(permission):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def permission_required_any(*permissions):
    """
    Require at least one of the given permissions.

    Anonymous users → Login
    Authenticated users without any permission → 403
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Authentication
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url="/login/",
                )

            # Authorization
            authz = Authorization(request.user)

            if not any(
                authz.can(permission)
                for permission in permissions
            ):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator