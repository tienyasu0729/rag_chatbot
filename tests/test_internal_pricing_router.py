from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.pricing import internal_auth
from app.routes import internal_pricing_router, pricing_reference_router


def _payload():
    return {
        "requestId": "req_1",
        "requestedBy": {"userId": 15, "role": "MANAGER", "branchId": 2},
        "vehicleInput": {
            "title": "Toyota Vios G CVT 2021",
            "categoryId": 1,
            "subcategoryId": 101,
            "year": 2021,
            "mileage": 42000,
            "fuel": "Xang",
            "transmission": "Tu dong",
        },
        "imageAssets": [
            {
                "url": "https://res.cloudinary.com/demo/image/upload/vehicle-pricing/front_001.jpg",
                "publicId": "vehicle-pricing/front_001",
                "source": "cloudinary",
                "declaredGroup": "front",
            }
        ],
    }


def test_internal_pricing_requires_token(monkeypatch):
    app = FastAPI()
    app.include_router(internal_pricing_router.router)
    client = TestClient(app)
    monkeypatch.setattr(internal_auth.get_settings(), "PRICING_INTERNAL_TOKEN", "secret")

    response = client.post("/internal/vehicle-pricing/estimate", json=_payload())

    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized_internal_service"


def test_internal_pricing_rejects_invalid_asset_domain(monkeypatch):
    app = FastAPI()
    app.include_router(internal_pricing_router.router)
    client = TestClient(app)
    monkeypatch.setattr(internal_auth.get_settings(), "PRICING_INTERNAL_TOKEN", "secret")
    monkeypatch.setattr(internal_auth.get_settings(), "PRICING_CLOUDINARY_ALLOWED_DOMAINS", "res.cloudinary.com")
    payload = _payload()
    payload["imageAssets"][0]["url"] = "https://evil.example.com/x.jpg"

    response = client.post(
        "/internal/vehicle-pricing/estimate",
        json=payload,
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_image_assets"


def test_internal_pricing_endpoint_uses_new_service_only(monkeypatch):
    app = FastAPI()
    app.include_router(internal_pricing_router.router)
    client = TestClient(app)
    monkeypatch.setattr(internal_auth.get_settings(), "PRICING_INTERNAL_TOKEN", "secret")
    called = {}

    def fake_estimate(payload):
        called["payload"] = payload
        return {
            "valuationId": "val_1",
            "resultType": "standard_estimate",
            "resultFlags": [],
            "dataBasis": {
                "source": "oto.com.vn",
                "type": "market_listing_price",
                "note": "Gia duoc tinh tu du lieu rao ban xe cu tren thi truong.",
            },
            "vehicleUnderstanding": {
                "detectedBrand": "Toyota",
                "detectedModel": "Vios",
                "brandKeyword": "toyota",
                "modelKeyword": "vios",
                "detectedVariant": "G CVT",
                "variantConfidence": 0.85,
                "normalizedFuel": "gasoline",
                "normalizedTransmission": "automatic",
                "taxonomyMismatch": False,
                "taxonomyWarning": None,
                "warning": None,
            },
            "marketReferencePrice": {
                "median": 510000000,
                "range": {"min": 500000000, "max": 530000000},
                "label": "Gia rao ban thi truong tham khao",
            },
            "fairPrice": {
                "suggestedPrice": 480000000,
                "range": {"min": 470000000, "max": 490000000},
                "label": "Gia hop ly sau khi xet condition va trust",
            },
            "dealSuggestion": {
                "recommendedOfferPrice": 460000000,
                "targetPurchasePrice": 465000000,
                "maxAcceptablePurchasePrice": 470000000,
                "label": "Goi y muc mua/deal",
                "negotiationRange": {"start": 460000000, "target": 465000000, "ceiling": 470000000},
                "talkingPoints": [],
            },
            "marketSellingPrice": {"suggestedPrice": 510000000, "minPrice": 500000000, "maxPrice": 530000000, "label": "Gia ban ra thi truong tham khao"},
            "purchasePrice": {"suggestedPrice": 460000000, "minPrice": 450000000, "maxPrice": 470000000, "label": "Gia thu vao de xuat"},
            "roughPurchaseRange": None,
            "pricingBreakdown": {"marketMedianPrice": 505000000, "conditionAdjustment": -5000000, "visualAdjustment": 0, "trustAdjustment": 0, "estimatedReconditioningCost": 15000000, "riskBuffer": 10000000, "targetMargin": 25000000},
            "conditionAssessment": {"overallScore": 7.6, "label": "Kha", "confidence": 0.7, "visibleDamage": False, "carQualityScore": 76, "exteriorScore": 78, "interiorScore": 74, "engineBayScore": 70, "damageFindings": [], "warnings": []},
            "riskAssessment": {"riskScore": 35, "riskLevel": "low", "direction": "higher_is_riskier", "riskFlags": []},
            "trustAssessment": {"trustScore": 0.78, "trustLabel": "Trung binh", "direction": "higher_is_more_trustworthy", "trustFlags": []},
            "imageProcessing": {
                "uploadedCount": 1,
                "validImageCount": 1,
                "exactDuplicatesRemoved": 0,
                "nearDuplicatesRemoved": 0,
                "analyzedCount": 1,
                "groups": {"front": 1},
                "coveredViews": ["front"],
                "partialViews": [],
                "missingViews": [],
                "inspectionGroups": ["front"],
                "ignoredImages": [],
            },
            "damageList": [],
            "pricingAdjustments": [],
            "marketSearch": {
                "toolName": "pricing_get_market_candidates",
                "marketWindowDays": 90,
                "fallbackWindowUsed": False,
                "fallbackLevel": 1,
                "inputCategoryId": 1,
                "inputSubcategoryId": 101,
                "inputCategoryName": "Toyota",
                "inputSubcategoryName": "Vios",
                "rawCount": 10,
                "scoredCount": 8,
                "usedCount": 8,
                "outliersRemoved": 1,
                "attempts": [],
                "diagnostics": [],
                "similarListingsFound": 10,
                "similarListingsUsed": 8,
            },
            "marketStats": {"similarListingsFound": 10, "similarListingsUsed": 8, "outliersRemoved": 1, "medianPrice": 505000000, "p25Price": 495000000, "p75Price": 520000000, "marketWindowDays": 90},
            "fallback": {"level": 1, "used": False, "description": "Co du lieu cung dong xe de dinh gia theo market query chinh."},
            "confidence": 0.78,
            "confidenceLabel": "Trung binh",
            "confidenceBreakdown": {
                "marketDataConfidence": 0.78,
                "variantMatchConfidence": 0.8,
                "imageCoverageConfidence": 0.75,
                "visionConfidence": 0.7,
                "overallConfidence": 0.78,
            },
            "variantMatchCoverage": {
                "inputVariant": "G CVT",
                "exactVariantMatches": 4,
                "partialVariantMatches": 2,
                "unknownVariantMatches": 1,
                "differentVariantMatches": 1,
                "candidateVariantConfidence": 0.82,
            },
            "warnings": [],
            "expertExplanation": {"summary": "x", "marketReasoning": [], "conditionReasoning": [], "purchaseReasoning": [], "limitations": [], "recommendedNextActions": []},
        }

    monkeypatch.setattr(internal_pricing_router, "estimate_vehicle_price", fake_estimate)

    response = client.post(
        "/internal/vehicle-pricing/estimate",
        json=_payload(),
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    assert called["payload"]["requestId"] == "req_1"
    assert called["payload"]["imageAssets"][0]["declaredGroup"] == "front"


def test_internal_pricing_reference_data_requires_token(monkeypatch):
    app = FastAPI()
    app.include_router(pricing_reference_router.router)
    client = TestClient(app)
    monkeypatch.setattr(internal_auth.get_settings(), "PRICING_INTERNAL_TOKEN", "secret")

    response = client.get("/internal/vehicle-pricing/reference-data")

    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized_internal_service"


def test_internal_pricing_reference_data_uses_separate_service(monkeypatch):
    app = FastAPI()
    app.include_router(pricing_reference_router.router)
    client = TestClient(app)
    monkeypatch.setattr(internal_auth.get_settings(), "PRICING_INTERNAL_TOKEN", "secret")
    called = {}

    def fake_reference_data():
        called["service"] = True
        return {
            "categories": [{"id": 1, "name": "Sedan", "vehicle_count": 12}],
            "subcategories": [{"id": 101, "name": "Vios", "category_id": 1, "category_name": "Sedan", "vehicle_count": 9}],
            "counts": {"categories": 1, "subcategories": 1},
        }

    monkeypatch.setattr(pricing_reference_router, "get_pricing_reference_options", fake_reference_data)

    response = client.get(
        "/internal/vehicle-pricing/reference-data",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    assert called["service"] is True
    assert response.json()["subcategories"][0]["name"] == "Vios"
