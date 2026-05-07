"""
Pricing errors va response helpers.
"""

from __future__ import annotations


class PricingError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 400, extra: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}

    def to_dict(self) -> dict:
        payload = {"error": self.code, "message": self.message}
        if self.extra:
            payload["details"] = self.extra
        return payload


class UnauthorizedInternalServiceError(PricingError):
    def __init__(self, message: str = "Internal service token khong hop le"):
        super().__init__("unauthorized_internal_service", message, status_code=401)

