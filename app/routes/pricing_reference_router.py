"""
Route phu tro frontend pricing UI lay category/subcategory tu SQL.
Tach rieng khoi pricing engine va khoi pricing_* tools.
"""

from __future__ import annotations

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.pricing.errors import PricingError
from app.pricing.internal_auth import verify_internal_token
from app.pricing.reference_data_service import get_pricing_reference_options

router = APIRouter(prefix="/internal/vehicle-pricing", tags=["internal-pricing-reference"])


@router.get("/reference-data")
async def internal_pricing_reference_data(authorization: str | None = Header(None)):
    try:
        verify_internal_token(authorization)
        return get_pricing_reference_options()
    except PricingError as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())
    except Exception as exc:
        error = PricingError("market_data_unavailable", f"Khong lay duoc reference data: {exc}", status_code=500)
        return JSONResponse(status_code=error.status_code, content=error.to_dict())
