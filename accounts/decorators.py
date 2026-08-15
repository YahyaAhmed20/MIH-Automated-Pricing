from functools import wraps

from django.core.exceptions import PermissionDenied

from .authorization import Authorization


def permission_required(permission):
    """
    Require a single permission.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            authz = Authorization(request.user)

            if not authz.can(permission):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def permission_required_any(*permissions):
    """
    Require at least one of the given permissions.

    Example:
        @permission_required_any(
            Permissions.PACKAGES_CREDIT_BASIC,
            Permissions.PACKAGES_CREDIT_FULL,
        )
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            authz = Authorization(request.user)

            if not any(authz.can(permission) for permission in permissions):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator