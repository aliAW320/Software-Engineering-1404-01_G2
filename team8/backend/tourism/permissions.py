import uuid
import jwt
import requests
from django.conf import settings
from rest_framework.permissions import BasePermission
from .models import User


def _extract_auth(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    token = request.COOKIES.get("access_token")
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    return token, auth_header


def _verify_with_core(request, auth_header):
    """
    Fallback auth check against core service.
    Useful when local JWT verification cannot decode the token (e.g. secret mismatch).
    """
    headers = {"Host": settings.CORE_HOST_HEADER}
    if auth_header:
        headers["Authorization"] = auth_header

    try:
        resp = requests.get(
            settings.CORE_AUTH_VERIFY_URL,
            headers=headers,
            cookies=request.COOKIES,
            timeout=settings.CORE_AUTH_TIMEOUT,
        )
    except requests.RequestException:
        return None, ""

    if resp.status_code != 200:
        return None, ""

    return resp.headers.get("X-User-Id"), (resp.headers.get("X-User-Email") or "")


def _fetch_core_user(request):
    """
    Validate JWT from core (cookie or Authorization) locally using shared secret.
    No network call; falls back to None if token invalid.
    """
    if hasattr(request, "_core_user"):
        return request._core_user

    token, auth_header = _extract_auth(request)

    if not token:
        # No bearer/cookie token; do not call core.
        request._core_user = None
        return None

    core_id = None
    email = ""
    try:
        payload = jwt.decode(
            token,
            settings.CORE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        core_id = payload.get("sub")
        email = payload.get("email") or ""
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Fallback to core verify endpoint when local decode fails.
        core_id, email = _verify_with_core(request, auth_header)
        if not core_id and not email:
            request._core_user = None
            return None

    user = None
    if core_id:
        user = User.objects.filter(core_user_id=core_id).first()
    if user is None and email:
        user = User.objects.filter(email=email).first()

    if user is None:
        username_seed = email.split("@")[0] if email else f"user-{core_id or uuid.uuid4()}"
        base = username_seed[:50] or "user"
        candidate = base
        counter = 1
        while User.objects.filter(username=candidate).exists():
            suffix = f"-{counter}"
            candidate = f"{base[:50-len(suffix)]}{suffix}"
            counter += 1
        user = User.objects.create(
            username=candidate,
            email=email or "",
            password_hash="core-auth",
            core_user_id=core_id or uuid.uuid4(),
        )
    else:
        changed = False
        if core_id and not user.core_user_id:
            user.core_user_id = core_id
            changed = True
        if email and user.email != email:
            user.email = email
            changed = True
        if changed:
            user.save(update_fields=["core_user_id", "email"])

    if email and email in settings.CORE_ADMIN_EMAILS and not user.is_admin:
        user.is_admin = True
        user.save(update_fields=["is_admin"])

    request._core_user = user
    request.user = user
    return user


class IsAuthenticated(BasePermission):
    """Authenticates by validating core JWT locally and attaching shadow user."""

    def has_permission(self, request, view):
        return _fetch_core_user(request) is not None


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: owners can write, everyone else read-only."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        user = _fetch_core_user(request)
        return user and obj.user_id == user.user_id


class AllowAny(BasePermission):
    """Allow any access. Only touch core if credentials are present."""

    def has_permission(self, request, view):
        # Only attempt attach when a token/header is present
        if request.META.get('HTTP_AUTHORIZATION') or request.COOKIES.get('access_token'):
            _fetch_core_user(request)
        return True


class IsAdmin(BasePermission):
    """Only users with is_admin=True."""

    def has_permission(self, request, view):
        user = _fetch_core_user(request)
        return user is not None and user.is_admin
