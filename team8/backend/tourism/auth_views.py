import requests
from http.cookies import SimpleCookie
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User
from .permissions import _fetch_core_user


def _proxy_core(path: str, request, method: str = "GET") -> HttpResponse:
    """Proxy a request to the core auth endpoints, preserving cookies and headers, forwarding Set-Cookie."""
    url = settings.CORE_API_BASE.rstrip("/") + path
    headers = {"Host": settings.CORE_HOST_HEADER}
    auth = request.META.get("HTTP_AUTHORIZATION")
    if auth:
        headers["Authorization"] = auth
    data = request.data if method != "GET" else None
    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            cookies=request.COOKIES,
            json=data,
            timeout=settings.CORE_AUTH_TIMEOUT,
        )
    except requests.RequestException:
        return HttpResponse('{"error": "core auth unavailable"}', status=503, content_type="application/json")

    django_resp = HttpResponse(resp.content, status=resp.status_code, content_type=resp.headers.get("Content-Type"))

    # Forward Set-Cookie headers exactly
    set_cookies = []
    raw_headers = getattr(resp, "raw", None)
    if raw_headers is not None and hasattr(raw_headers.headers, "getlist"):
        set_cookies = raw_headers.headers.getlist("Set-Cookie")
    elif "Set-Cookie" in resp.headers:
        set_cookies = [resp.headers.get("Set-Cookie")]

    for cookie_header in set_cookies:
        c = SimpleCookie()
        c.load(cookie_header)
        for morsel in c.values():
            django_resp.set_cookie(
                morsel.key,
                morsel.value,
                expires=morsel["expires"] or None,
                path=morsel["path"] or "/",
                domain=morsel["domain"] or None,
                secure=bool(morsel["secure"]),
                httponly=bool(morsel["httponly"]),
                samesite=morsel["samesite"] or None,
                max_age=morsel["max-age"] or None,
            )

    return django_resp


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    return _proxy_core("/auth/login/", request, method="POST")


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    return _proxy_core("/auth/signup/", request, method="POST")


@api_view(["POST"])
def logout(request):
    return _proxy_core("/auth/logout/", request, method="POST")


@api_view(["GET"])
def verify_token(request):
    return _proxy_core("/auth/verify/", request, method="GET")


@api_view(["GET"])
@permission_classes([AllowAny])
def get_profile(request):
    """
    Return local auth profile (always available with valid token) and
    enrich with core profile fields when core /me is reachable.
    """
    user = _fetch_core_user(request)
    if user is None:
        return Response({"error": "not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    profile = {
        "user_id": user.user_id,
        "username": user.username,
        "is_admin": user.is_admin,
        "email": user.email,
    }

    # Best-effort enrichment from core profile; do not fail auth if core is slow/unreachable.
    url = settings.CORE_AUTH_ME_URL
    headers = {"Host": settings.CORE_HOST_HEADER}
    auth = request.META.get("HTTP_AUTHORIZATION")
    if auth:
        headers["Authorization"] = auth

    try:
        resp = requests.get(url, headers=headers, cookies=request.COOKIES, timeout=settings.CORE_AUTH_TIMEOUT)
        if resp.status_code == 200:
            try:
                core_data = resp.json() if resp.content else {}
            except ValueError:
                core_data = {}
            core_user = core_data.get("user", {}) if isinstance(core_data, dict) else {}
            if isinstance(core_user, dict):
                for field in ("first_name", "last_name", "age"):
                    if core_user.get(field) is not None:
                        profile[field] = core_user.get(field)
                if not profile.get("email") and core_user.get("email"):
                    profile["email"] = core_user.get("email")
    except requests.RequestException:
        pass

    return Response({"ok": True, "user": profile}, status=status.HTTP_200_OK)
