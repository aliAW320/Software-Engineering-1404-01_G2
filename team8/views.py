"""
Lightweight reverse-proxy so /team8/* on the core site forwards to the
team8 gateway container (listening on app404_net).

No external dependencies: uses urllib from stdlib.
"""
import os
import urllib.request
import urllib.error
from django.http import StreamingHttpResponse, HttpResponse

# Default host: service name inside app404_net
GATEWAY_ORIGIN = os.environ.get("TEAM8_GATEWAY_ORIGIN", "http://gateway")


def _build_target(path, query):
    # Incoming path already excludes the /team8/ prefix
    if path.startswith("/"):
        path = path[1:]

    # Special-case media so the path matches the MinIO-signed URL (/team8-media/…)
    if path.startswith("team8-media/"):
        target_path = f"/{path}"
    else:
        target_path = f"/team8/{path}"

    base = GATEWAY_ORIGIN.rstrip("/")
    url = f"{base}{target_path}"
    if query:
        url = f"{url}?{query}"
    return url


def gateway_proxy(request, path=""):
    target = _build_target(path, request.META.get("QUERY_STRING", ""))

    body = request.body if request.method not in ("GET", "HEAD") else None

    # Copy headers except host/content-length (urllib manages those)
    headers = {
        k[5:].replace("_", "-"): v
        for k, v in request.META.items()
        if k.startswith("HTTP_")
        and k not in ("HTTP_HOST",)
    }
    # Preserve original host/proto for SigV4 validation downstream
    headers["Host"] = request.get_host()
    if "HTTP_X_FORWARDED_PROTO" in request.META:
        headers["X-Forwarded-Proto"] = request.META["HTTP_X_FORWARDED_PROTO"]
    else:
        headers["X-Forwarded-Proto"] = request.scheme
    # Preserve original content type (with boundary if multipart)
    raw_ct = request.META.get("CONTENT_TYPE") or request.META.get("HTTP_CONTENT_TYPE")
    if raw_ct:
        headers["Content-Type"] = raw_ct

    req = urllib.request.Request(
        url=target,
        data=body,
        headers=headers,
        method=request.method,
    )

    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        # HTTPError is both an exception and a response
        return HttpResponse(
            e.read(),
            status=e.code,
            reason=e.reason,
            content_type=e.headers.get_content_type(),
        )
    except urllib.error.URLError as e:
        return HttpResponse(f"Gateway unreachable: {e.reason}", status=502)

    def stream():
        chunk = resp.read(8192)
        while chunk:
            yield chunk
            chunk = resp.read(8192)

    django_resp = StreamingHttpResponse(
        streaming_content=stream(),
        status=resp.status,
        reason=resp.reason,
        content_type=resp.headers.get_content_type(),
    )

    # Propagate key headers
    for header, value in resp.headers.items():
        h = header.lower()
        if h in ("content-length", "transfer-encoding", "content-type"):
            continue  # handled by Django/Response
        django_resp[header] = value

    return django_resp
