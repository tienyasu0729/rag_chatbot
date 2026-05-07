import io

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import pricing_router


def _multipart_file(name: str) -> tuple[str, tuple[str, io.BytesIO, str]]:
    return ("images", (name, io.BytesIO(b"fake-image"), "image/jpeg"))


def test_pricing_endpoint_hides_comparables_by_default(monkeypatch):
    app = FastAPI()
    app.include_router(pricing_router.router)
    client = TestClient(app)

    async def fake_prepare(images, image_tags):
        class Bundle:
            accepted_count = 1
            skipped_count = 0
            bucket_counts = {"exterior_overview": 1, "interior": 0, "detail_damage": 0}

        return Bundle()

    monkeypatch.setattr(pricing_router, "prepare_images_for_assessment", fake_prepare)
    monkeypatch.setattr(
        pricing_router,
        "analyze_vehicle_condition",
        lambda bundle: {
            "condition_score": 60,
            "score_breakdown": {
                "paint_exterior": 15,
                "body_damage": 15,
                "interior": 15,
                "mechanical_visible": 9,
                "tires_wheels": 6,
            },
            "damage_percentage": {"scratch": "unknown", "dent": "unknown"},
            "risk_flags": ["default"],
            "damage_summary": "summary",
        },
    )
    monkeypatch.setattr(
        pricing_router,
        "_get_market_data",
        lambda **kwargs: {
            "comparable_count": 2,
            "market_min": 100,
            "market_avg": 120,
            "market_max": 140,
            "comparables": [{"id": 1, "title": "A", "status": "Available", "priority_match": 1}],
        },
    )
    monkeypatch.setattr(
        pricing_router,
        "estimate_purchase_price",
        lambda **kwargs: {
            "suggested_purchase_price": 90,
            "price_range_min": 80,
            "price_range_max": 100,
            "deduction_factors": ["x"],
        },
    )

    response = client.post(
        "/api/pricing/estimate",
        data={
            "subcategory_name": "Toyota Vios",
            "image_tags": "exterior_overview",
        },
        files=[_multipart_file("car.jpg")],
    )

    assert response.status_code == 200
    body = response.json()
    assert "comparables" not in body
    assert body["pricing"]["suggested_purchase_price"] == 90


def test_pricing_endpoint_rejects_tag_count_mismatch():
    app = FastAPI()
    app.include_router(pricing_router.router)
    client = TestClient(app)

    response = client.post(
        "/api/pricing/estimate",
        data={
            "subcategory_name": "Toyota Vios",
            "image_tags": ["exterior_overview", "interior"],
        },
        files=[_multipart_file("car.jpg")],
    )

    assert response.status_code == 422
