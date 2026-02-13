import requests
from http.cookies import SimpleCookie
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User


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
def get_profile(request):
    """Return core profile plus local username/id/admin info."""
    url = settings.CORE_AUTH_ME_URL
    headers = {"Host": settings.CORE_HOST_HEADER}
    auth = request.META.get("HTTP_AUTHORIZATION")
    if auth:
        headers["Authorization"] = auth
    try:
        resp = requests.get(url, headers=headers, cookies=request.COOKIES, timeout=settings.CORE_AUTH_TIMEOUT)
    except requests.RequestException:
        return Response({"error": "core auth unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    core_data = resp.json() if resp.content else {}
    if resp.status_code != 200:
        return Response(core_data, status=resp.status_code)

    # Decode access token locally to get core user id/email
    token = request.COOKIES.get("access_token")
    if not token and auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()

    core_id = None
    email = None
    if token:
        try:
            payload = jwt.decode(token, settings.CORE_JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            core_id = payload.get("sub")
            email = payload.get("email")
        except Exception:
            pass

    user = None
    if core_id:
        user = User.objects.filter(core_user_id=core_id).first()
    if user is None and email:
        user = User.objects.filter(email=email).first()

    if user:
        core_data.setdefault("user", {})
        core_data["user"].update(
            {
                "user_id": user.user_id,
                "username": user.username,
                "is_admin": user.is_admin,
                "email": user.email or email or core_data["user"].get("email", ""),
            }
        )
    return Response(core_data, status=resp.status_code)
