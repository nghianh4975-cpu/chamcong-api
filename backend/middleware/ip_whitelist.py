from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Callable
import os


class IPRestrictMiddleware(BaseHTTPMiddleware):
    """
    Middleware chặn truy cập từ IP không được phép.
    Chỉ cho phép IP trong whitelist ALLOWED_IPS.
    Nếu ALLOWED_IPS rỗng hoặc chứa '*' → cho phép tất cả (dev mode).
    """

    # IP hệ thống (localhost / Render infrastructure)
    SYSTEM_IPS = {
        "127.0.0.1", "::1", "::ffff:127.0.0.1",
        "localhost",
    }

    def __init__(self, app, allowed_ips: set = None):
        super().__init__(app)
        self.allowed_ips: set = allowed_ips or set()
        # Thêm system IPs luôn được phép
        self.allowed_ips.update(self.SYSTEM_IPS)

    def _get_client_ip(self, request: Request) -> str:
        """Lấy IP thật của client từ headers hoặc socket."""
        # Render proxy → real IP nằm trong X-Forwarded-For
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            # Lấy IP đầu tiên (client thật)
            return forwarded.split(",")[0].strip()

        # X-Real-IP header (nginx / some proxies)
        real_ip = request.headers.get("x-real-ip", "")
        if real_ip:
            return real_ip.strip()

        # Fallback: socket address
        if request.client:
            return request.client.host
        return ""

    def _is_allowed(self, client_ip: str) -> bool:
        """Kiểm tra IP có trong whitelist không."""
        if not self.allowed_ips or "*" in self.allowed_ips:
            return True  # Không giới hạn IP

        # Exact match
        if client_ip in self.allowed_ips:
            return True

        # CIDR support (VD: 192.168.1.0/24)
        for allowed in self.allowed_ips:
            if "/" in allowed:
                if self._ip_in_cidr(client_ip, allowed):
                    return True

        return False

    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """Kiểm tra IP có trong CIDR range không."""
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except Exception:
            return False

    async def dispatch(self, request: Request, call_next: Callable):
        # Bỏ qua health check và static files
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json", "/redoc") or path.startswith("/static"):
            return await call_next(request)

        # Bỏ qua OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if not self._is_allowed(client_ip):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Truy cap bi chan. Chi may tinh tai quan moi duoc phep truy cap."
                }
            )

        return await call_next(request)


def get_allowed_ips_from_env() -> set:
    """Đọc whitelist IP từ biến môi trường ALLOWED_IPS."""
    raw = os.getenv("ALLOWED_IPS", "")
    if not raw or raw.strip() == "":
        return set()  # Rỗng = cho phép tất cả (dev)

    # Split bằng dấu phẩy, bỏ khoảng trắng
    ips = {ip.strip() for ip in raw.split(",") if ip.strip()}
    return ips
