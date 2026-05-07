"""
Router dinh gia nhap xe tu anh.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.models.schemas import PricingEstimateRequest, PricingEstimateResponse
from app.services.image_processor import prepare_images_for_assessment
from app.services.pricing import _get_market_data, estimate_purchase_price
from app.services.vision_analysis import analyze_vehicle_condition
from app.db import sqlserver

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


@router.get("/subcategories")
async def list_subcategories():
    """
    Lay danh sach subcategory de hien thi dropdown tren UI dinh gia.
    """
    sql = """
WITH vehicle_scope AS (
    SELECT
        v.id,
        v.subcategory_id,
        v.category_id
    FROM Vehicles v
    WHERE
        v.is_deleted = 0
        AND v.status IN ('Available', 'Sold', 'Reserved')
),
category_votes AS (
    SELECT
        vs.subcategory_id,
        vs.category_id,
        COUNT(*) AS vote_count
    FROM vehicle_scope vs
    GROUP BY vs.subcategory_id, vs.category_id
),
best_category AS (
    SELECT
        cv.subcategory_id,
        cv.category_id,
        cv.vote_count,
        ROW_NUMBER() OVER (
            PARTITION BY cv.subcategory_id
            ORDER BY cv.vote_count DESC, cv.category_id ASC
        ) AS rn
    FROM category_votes cv
),
subcat_counts AS (
    SELECT
        vs.subcategory_id,
        COUNT(*) AS vehicle_count
    FROM vehicle_scope vs
    GROUP BY vs.subcategory_id
)
SELECT
    sc.id,
    sc.name,
    sc.name_normalized,
    sc.status,
    c.name AS category_name,
    scc.vehicle_count
FROM Subcategories sc
JOIN subcat_counts scc ON scc.subcategory_id = sc.id
JOIN best_category bc ON bc.subcategory_id = sc.id AND bc.rn = 1
JOIN Categories c ON c.id = bc.category_id
WHERE sc.status = 'active'
ORDER BY c.name ASC, sc.name ASC
"""
    try:
        rows = sqlserver.query_positional_readonly(sql)
        return {
            "count": len(rows),
            "items": [
                {
                    "id": int(r["id"]),
                    "name": str(r.get("name") or ""),
                    "name_normalized": str(r.get("name_normalized") or ""),
                    "status": str(r.get("status") or ""),
                    "category_name": str(r.get("category_name") or ""),
                    "vehicle_count": int(r.get("vehicle_count") or 0),
                }
                for r in rows
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Khong lay duoc danh sach subcategory") from exc


@router.post(
    "/estimate",
    response_model=PricingEstimateResponse,
    response_model_exclude_none=True,
)
async def estimate_vehicle_purchase_price(
    images: list[UploadFile] = File(...),
    image_tags: list[str] = Form(...),
    subcategory_id: int | None = Form(None),
    subcategory_name: str | None = Form(None),
    year: int | None = Form(None),
    fuel: str | None = Form(None),
    transmission: str | None = Form(None),
    origin: str | None = Form(None),
    include_comparables: bool = Form(False),
):
    if not images:
        raise HTTPException(status_code=422, detail="Phai upload it nhat 1 anh")
    if len(images) != len(image_tags):
        raise HTTPException(status_code=422, detail="So luong images va image_tags phai khop nhau")

    try:
        request = PricingEstimateRequest.model_validate(
            {
                "subcategory_id": subcategory_id,
                "subcategory_name": subcategory_name,
                "year": year,
                "fuel": fuel,
                "transmission": transmission,
                "origin": origin,
                "include_comparables": include_comparables,
                "image_tags": image_tags,
            }
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    try:
        processed_images = await prepare_images_for_assessment(images, request.image_tags)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    vehicle_assessment = analyze_vehicle_condition(processed_images)

    try:
        market_data = _get_market_data(
            subcategory_id=request.subcategory_id,
            subcategory_name=request.subcategory_name,
            year=request.year,
            fuel=request.fuel,
            transmission=request.transmission,
            origin=request.origin,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Khong truy van duoc du lieu thi truong") from exc

    pricing_result = estimate_purchase_price(
        market_data=market_data,
        vehicle_assessment=vehicle_assessment,
        vehicle_config={
            "subcategory_id": request.subcategory_id,
            "subcategory_name": request.subcategory_name,
            "year": request.year,
            "fuel": request.fuel,
            "transmission": request.transmission,
            "origin": request.origin,
            "accepted_images": processed_images.accepted_count,
            "skipped_images": processed_images.skipped_count,
            "bucket_counts": processed_images.bucket_counts,
        },
    )

    response = {
        "vehicle_assessment": {
            "condition_score": vehicle_assessment["condition_score"],
            "score_breakdown": vehicle_assessment["score_breakdown"],
            "damage_percentage": vehicle_assessment["damage_percentage"],
            "risk_flags": vehicle_assessment["risk_flags"],
            "damage_summary": vehicle_assessment["damage_summary"],
        },
        "market_data": {
            "comparable_count": market_data["comparable_count"],
            "min": market_data["market_min"],
            "avg": market_data["market_avg"],
            "max": market_data["market_max"],
        },
        "pricing": {
            "suggested_purchase_price": pricing_result["suggested_purchase_price"],
            "price_range_min": pricing_result["price_range_min"],
            "price_range_max": pricing_result["price_range_max"],
            "deduction_factors": pricing_result["deduction_factors"],
        },
    }
    if request.include_comparables:
        response["comparables"] = market_data["comparables"]

    return response
