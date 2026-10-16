"""Single-user loopback boundary; no forwarded headers or login state are trusted."""
from ipaddress import ip_address
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


LOCAL_ORIGINS = [
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1", "[::1]")
    for port in (5173, 8000)
]


class LocalAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            local_client = request.client is not None and ip_address(request.client.host).is_loopback
            host = urlsplit("//" + request.headers.get("host", ""))
            local_host = (host.hostname in {"localhost", "127.0.0.1", "::1"}
                          and host.username is None and host.password is None
                          and not host.path and not host.query and not host.fragment)
            host.port  # Reject invalid port syntax as well.
        except ValueError:
            local_client = local_host = False
        if not local_client or not local_host:
            return JSONResponse(status_code=403, content={"detail": "Loopback access is required."})
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if ((origin is not None and origin not in LOCAL_ORIGINS)
                    or (origin is None and request.headers.get("sec-fetch-site") == "cross-site")
                    or media_type != "application/json"):
                return JSONResponse(status_code=403, content={"detail": "Local JSON mutations only."})
        return await call_next(request)
