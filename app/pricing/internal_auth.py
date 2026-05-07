"""
Xac thuc token noi bo dung chung cho cac route internal pricing.
"""

from __future__ import annotations

from app.config import get_settings
from app.pricing.errors import UnauthorizedInternalServiceError


def verify_internal_token(authorization: str | None) -> None:
    expected = get_settings().PRICING_INTERNAL_TOKEN.strip()
    if not expected:
        raise UnauthorizedInternalServiceError("Chua cau hinh PRICING_INTERNAL_TOKEN")
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedInternalServiceError()
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise UnauthorizedInternalServiceError()
