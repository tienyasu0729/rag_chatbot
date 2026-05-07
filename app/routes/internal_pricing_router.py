"""
Internal pricing router cho Java Spring Boot.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Header
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.pricing.errors import PricingError
from app.pricing.internal_auth import verify_internal_token
from app.pricing.schemas import InternalPricingEstimateRequest, InternalPricingEstimateResponse
from app.pricing.service import estimate_vehicle_price

router = APIRouter(prefix="/internal/vehicle-pricing", tags=["internal-pricing"])


@router.post("/estimate", response_model=InternalPricingEstimateResponse, response_model_exclude_none=True)
async def internal_estimate_vehicle_price(
    payload: dict = Body(...),
    authorization: str | None = Header(None),
):
    try:
        verify_internal_token(authorization)
        request_model = InternalPricingEstimateRequest.model_validate(payload)
        return estimate_vehicle_price(request_model.model_dump(mode="json"))
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content=PricingError(
                "invalid_request",
                "Request body khong hop le",
                status_code=422,
                extra={"validationErrors": exc.errors()},
            ).to_dict(),
        )
    except PricingError as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())
