from types import SimpleNamespace

from app.pricing import market_statistics
from app.pricing import service
from app.pricing.image_analysis_service import validate_and_process_assets
from app.pricing.text_analysis_service import analyze_vehicle_text, normalize_transmission
from app.pricing.vision_inspection_service import sanitize_group_inspection


def test_collect_market_candidates_uses_fallback_levels(monkeypatch):
    calls = []

    def fake_execute(tool_name, params):
        calls.append((tool_name, params))
        if tool_name == "pricing_get_market_candidates" and params["year_range"] in {1, 2}:
            return {"items": [], "count": 0}
        return {
            "items": [
                {
                    "listingId": str(idx),
                    "title": f"Toyota Vios G CVT 202{idx % 2}",
                    "price": 480000000 + idx * 5000000,
                    "categoryId": 1,
                    "subcategoryId": 101,
                    "year": 2021,
                    "mileage": 40000 + idx * 1000,
                    "fuel": "May xang",
                    "transmission": "So tu dong",
                    "bodyStyle": "Sedan",
                    "origin": "Lap rap trong nuoc",
                    "postingDate": "2026-04-10",
                }
                for idx in range(1, 6)
            ],
            "count": 5,
        }

    monkeypatch.setattr(service, "execute_pricing_tool", fake_execute)
    result = service.collect_market_candidates(
        {
            "categoryId": 1,
            "subcategoryId": 105,
            "branchId": 2,
            "year": 2021,
            "mileage": 40000,
            "fuel": "Xang",
            "transmission": "Tu dong",
            "bodyStyle": "Sedan",
            "origin": "Trong nuoc",
        },
        {"modelKeyword": "vios"},
        {"taxonomyMismatch": True},
    )

    assert calls[0][1]["year_range"] == 1
    assert calls[1][1]["year_range"] == 2
    assert calls[2][1]["subcategory_id"] is None
    assert result["fallbackLevel"] == 4
    assert result["taxonomyFallbackUsed"] is True
    assert result["attempts"][2]["rawCount"] == 5


def test_estimate_vehicle_price_persists_schema_version(monkeypatch):
    saved = {}

    monkeypatch.setattr(service, "save_valuation", lambda doc: saved.update(doc))
    monkeypatch.setattr(service, "execute_pricing_tool", lambda tool_name, params: _fake_tools(tool_name, params))
    monkeypatch.setattr(
        service,
        "inspect_vehicle_images",
        lambda processed, vehicle_input: {
            "inspectionGroups": {},
            "damageFindings": [],
            "riskFlags": [],
            "rawModelOutputs": [],
            "sanitizedInspection": {},
        },
    )
    monkeypatch.setattr(
        service,
        "collect_market_candidates",
        lambda vehicle_input, text_analysis, taxonomy: {
            "items": _fake_tools("pricing_get_market_candidates", {})["items"] * 3,
            "count": 15,
            "rawCount": 15,
            "fallbackLevel": 1,
            "marketWindowDays": 90,
            "toolName": "pricing_get_market_candidates",
            "attempts": [{"level": 1, "toolName": "pricing_get_market_candidates", "paramsUsed": {"subcategory_id": 101}, "rawCount": 15}],
            "diagnostics": [],
            "taxonomyFallbackUsed": False,
        },
    )

    payload = {
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
            "bodyStyle": "Sedan",
            "origin": "Trong nuoc",
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

    response = service.estimate_vehicle_price(payload)

    assert response["valuationId"] == saved["_id"]
    assert saved["schemaVersion"] == "vehicle-pricing-v2"
    assert response["fairPrice"]["suggestedPrice"] is not None
    assert response["dealSuggestion"]["recommendedOfferPrice"] is not None
    assert response["imageProcessing"]["groups"]["front"] == 1
    assert "pricingAdjustments" in response
    assert response["marketSearch"]["rawCount"] == 15
    assert response["vehicleUnderstanding"]["modelKeyword"] == "vios"
    assert "confidenceBreakdown" in response
    assert "variantMatchCoverage" in response
    assert saved["imageAnalysis"]["rawModelOutputs"] == []


def test_invalid_declared_group_rejected():
    from app.pricing.errors import PricingError

    try:
        validate_and_process_assets(
            [
                {
                    "url": "https://res.cloudinary.com/demo/image/upload/vehicle-pricing/front_001.jpg",
                    "publicId": "vehicle-pricing/front_001",
                    "source": "cloudinary",
                    "declaredGroup": "invalid_group",
                }
            ]
        )
    except PricingError as exc:
        assert exc.code == "invalid_image_assets"
    else:
        raise AssertionError("Expected invalid_image_assets")


def test_normalize_transmission_keeps_vietnamese_d():
    assert normalize_transmission("Tá»± Ä‘á»™ng") == "automatic"
    assert normalize_transmission("Sá»‘ tá»± Ä‘á»™ng") == "automatic"


def test_analyze_vehicle_text_extracts_model_keyword():
    result = analyze_vehicle_text(
        {
            "title": "Toyota Vios G 1.5 CVT 2021",
            "fuel": "MÃ¡y xÄƒng",
            "transmission": "Tá»± Ä‘á»™ng",
        }
    )
    assert result["detectedBrand"] == "Toyota"
    assert result["detectedModel"] == "Vios"
    assert result["modelKeyword"] == "vios"
    assert result["normalizedFuel"] == "gasoline"
    assert result["normalizedTransmission"] == "automatic"


def test_duoi_xe_resolves_to_rear_and_not_missing():
    processed = validate_and_process_assets(
        [
            {
                "url": "https://res.cloudinary.com/demo/image/upload/vehicle-pricing/duoi_xe.jpg",
                "publicId": "vehicle-pricing/duoi_xe",
                "source": "cloudinary",
                "declaredGroup": "other",
            }
        ]
    )

    asset = processed["acceptedAssets"][0]
    assert asset.filename_hint_group == "rear"
    assert "rear" in asset.resolved_groups
    assert "rear" not in processed["missingViews"]
    assert asset.group_mismatch is True


def test_document_asset_is_excluded_from_condition_scoring():
    processed = validate_and_process_assets(
        [
            {
                "url": "https://res.cloudinary.com/demo/image/upload/vehicle-pricing/document.jpg",
                "publicId": "vehicle-pricing/document",
                "source": "cloudinary",
                "declaredGroup": "document",
            }
        ]
    )

    asset = processed["acceptedAssets"][0]
    assert asset.resolved_groups == ["document"]
    assert asset.include_in_condition_scoring is False
    assert asset.inspection_group is None


def test_public_id_placeholder_is_sanitized():
    assets = [SimpleNamespace(public_id="vehicle-pricing/interior_front", url="https://res.cloudinary.com/demo/image/upload/x.jpg")]
    payload = {
        "detectedGroup": "interior_front",
        "imageQuality": "good",
        "score": 73,
        "confidence": 0.82,
        "findings": [
            {
                "issue": "seat_wear",
                "label": "Ghe lai hao mon",
                "location": "driver_seat",
                "severity": "medium",
                "confidence": 0.8,
                "evidenceImages": ["public_id"],
            }
        ],
        "riskFlags": [],
    }

    result = sanitize_group_inspection("interior_front", assets, payload)

    assert result["findings"][0]["evidenceImages"] == ["vehicle-pricing/interior_front"]


def test_low_data_model_estimate_still_returns_purchase_price(monkeypatch):
    monkeypatch.setattr(service, "save_valuation", lambda doc: None)
    monkeypatch.setattr(service, "execute_pricing_tool", lambda tool_name, params: _fake_tools(tool_name, params))
    monkeypatch.setattr(
        service,
        "inspect_vehicle_images",
        lambda processed, vehicle_input: {
            "inspectionGroups": {"front": {"score": 78, "confidence": 0.7, "findings": [], "riskFlags": []}},
            "damageFindings": [],
            "riskFlags": [],
            "rawModelOutputs": [],
            "sanitizedInspection": {},
        },
    )
    monkeypatch.setattr(
        service,
        "collect_market_candidates",
        lambda vehicle_input, text_analysis, taxonomy: {
            "items": _fake_tools("pricing_get_market_candidates", {})["items"][:3],
            "count": 3,
            "rawCount": 3,
            "fallbackLevel": 1,
            "marketWindowDays": 90,
            "toolName": "pricing_get_market_candidates",
            "attempts": [{"level": 1, "toolName": "pricing_get_market_candidates", "paramsUsed": {"subcategory_id": 101}, "rawCount": 3}],
            "diagnostics": [],
            "taxonomyFallbackUsed": False,
        },
    )

    response = service.estimate_vehicle_price(_base_payload())

    assert response["resultType"] == "low_data_model_estimate"
    assert response["purchasePrice"]["suggestedPrice"] is not None
    assert "do tin cay thap" in response["purchasePrice"]["label"].lower()
    assert "low_market_data" in response["resultFlags"]


def test_rough_segment_estimate_has_no_purchase_suggested(monkeypatch):
    monkeypatch.setattr(service, "save_valuation", lambda doc: None)
    monkeypatch.setattr(service, "execute_pricing_tool", lambda tool_name, params: _fake_tools(tool_name, params))
    monkeypatch.setattr(
        service,
        "inspect_vehicle_images",
        lambda processed, vehicle_input: {
            "inspectionGroups": {},
            "damageFindings": [],
            "riskFlags": [],
            "rawModelOutputs": [],
            "sanitizedInspection": {},
        },
    )
    monkeypatch.setattr(
        service,
        "collect_market_candidates",
        lambda vehicle_input, text_analysis, taxonomy: {
            "items": _fake_tools("pricing_get_market_candidates", {})["items"][:6],
            "count": 6,
            "rawCount": 6,
            "fallbackLevel": 4,
            "marketWindowDays": 90,
            "toolName": "pricing_get_segment_candidates",
            "attempts": [{"level": 4, "toolName": "pricing_get_segment_candidates", "paramsUsed": {"body_style": "Sedan"}, "rawCount": 6}],
            "diagnostics": ["Dang dung segment fallback."],
            "taxonomyFallbackUsed": True,
        },
    )

    response = service.estimate_vehicle_price(_base_payload())

    assert response["resultType"] == "rough_segment_estimate"
    assert response["purchasePrice"]["suggestedPrice"] is None
    assert response["dealSuggestion"]["recommendedOfferPrice"] is None
    assert response["roughPurchaseRange"] is not None


def test_confidence_is_capped_when_exact_variant_missing(monkeypatch):
    monkeypatch.setattr(service, "save_valuation", lambda doc: None)
    monkeypatch.setattr(service, "execute_pricing_tool", lambda tool_name, params: _fake_tools(tool_name, params))
    monkeypatch.setattr(
        service,
        "inspect_vehicle_images",
        lambda processed, vehicle_input: {
            "inspectionGroups": {"front": {"score": 80, "confidence": 0.8, "findings": [], "riskFlags": []}},
            "damageFindings": [],
            "riskFlags": [],
            "rawModelOutputs": [],
            "sanitizedInspection": {},
        },
    )
    monkeypatch.setattr(
        service,
        "collect_market_candidates",
        lambda vehicle_input, text_analysis, taxonomy: {
            "items": [
                {**item, "title": f"Toyota Vios E MT 202{idx % 2 + 3}", "transmission": "So san"}
                for idx, item in enumerate(_fake_tools("pricing_get_market_candidates", {})["items"] * 3, start=1)
            ],
            "count": 15,
            "rawCount": 15,
            "fallbackLevel": 3,
            "selectedAttemptLevel": 3,
            "marketWindowDays": 365,
            "marketWindow": {"initialDays": 90, "usedDays": 365, "fallbackWindowUsed": True, "reason": "Mo rong query."},
            "toolName": "pricing_get_market_candidates",
            "attempts": [],
            "diagnostics": ["Da bo subcategory de mo rong query."],
            "taxonomyFallbackUsed": True,
            "taxonomyMismatch": False,
        },
    )

    response = service.estimate_vehicle_price(_base_payload())

    assert response["resultType"] == "variant_uncertain_estimate"
    assert response["confidence"] <= 0.60
    assert response["confidenceLabel"] == "Trung binh thap"
    assert "variant_uncertain" in response["resultFlags"]
    assert "subcategory_broadened" in response["resultFlags"]
    assert "taxonomy_mismatch_warning" not in response["resultFlags"]


def test_mileage_zero_comparable_gets_quality_flags_and_weight_penalty():
    vehicle_input = _base_payload()["vehicleInput"] | {"branchId": 2}
    text_analysis = analyze_vehicle_text(vehicle_input)
    listings = [
        {
            "listingId": "m0",
            "title": "Toyota Vios G CVT 2021",
            "price": 500000000,
            "categoryId": 1,
            "subcategoryId": 101,
            "year": 2021,
            "mileage": 0,
            "fuel": "May xang",
            "transmission": "So tu dong",
            "bodyStyle": "Sedan",
            "origin": "Lap rap trong nuoc",
            "branchId": 2,
            "postingDate": "2026-04-10",
        }
    ]

    result = market_statistics.score_and_filter_candidates(vehicle_input, text_analysis, listings)
    candidate = result["candidates"][0]

    assert "mileage_unknown_or_zero" in candidate["dataQualityFlags"]
    assert candidate["weight"] < 1.0
    assert any("mileage" in reason.lower() for reason in candidate["weightAdjustmentReasons"])


def test_invalid_vision_output_is_not_used_for_condition_scoring():
    assets = [SimpleNamespace(public_id="vehicle-pricing/front", url="https://res.cloudinary.com/demo/image/upload/x.jpg")]
    payload = {
        "detectedGroup": "front|rear|left_side",
        "imageQuality": "good|acceptable",
        "score": 82,
        "confidence": 0.9,
        "findings": [
            {
                "issue": "scratch",
                "label": "Tray nhe",
                "location": "front_bumper",
                "severity": "minor",
                "confidence": 0.9,
                "evidenceImages": ["vehicle-pricing/front"],
            }
        ],
        "riskFlags": [],
    }

    result = sanitize_group_inspection("front", assets, payload)

    assert result["validVisionOutput"] is False
    assert result["usedForConditionScoring"] is False
    assert result["detectedGroup"] is None
    assert result["imageQuality"] == "unknown"
    assert result["findings"] == []


def test_caption_hint_resolves_group_and_caption_only_claim_stays_outside_pricing(monkeypatch):
    monkeypatch.setattr(service, "save_valuation", lambda doc: None)
    monkeypatch.setattr(service, "execute_pricing_tool", lambda tool_name, params: _fake_tools(tool_name, params))
    monkeypatch.setattr(
        service,
        "inspect_vehicle_images",
        lambda processed, vehicle_input: {
            "inspectionGroups": {"rear": {"score": 78, "confidence": 0.8, "findings": [], "riskFlags": []}},
            "damageFindings": [],
            "riskFlags": [],
            "rawModelOutputs": [],
            "sanitizedInspection": {"rear": {"findings": []}},
        },
    )
    monkeypatch.setattr(
        service,
        "collect_market_candidates",
        lambda vehicle_input, text_analysis, taxonomy: {
            "items": _fake_tools("pricing_get_market_candidates", {})["items"],
            "count": 5,
            "rawCount": 5,
            "fallbackLevel": 1,
            "selectedAttemptLevel": 1,
            "marketWindowDays": 90,
            "marketWindow": {"initialDays": 90, "usedDays": 90, "fallbackWindowUsed": False, "reason": None},
            "toolName": "pricing_get_market_candidates",
            "attempts": [],
            "diagnostics": [],
            "taxonomyFallbackUsed": False,
            "taxonomyMismatch": False,
        },
    )
    payload = _base_payload()
    payload["imageAssets"][1]["caption"] = "Anh duoi xe, co xuoc nhe"
    response = service.estimate_vehicle_price(payload)

    assert response["imageProcessing"]["missingViews"].count("rear") == 0
    assert response["imageCaptionAnalysis"]["captionProvidedCount"] == 1
    assert response["imageCaptionAnalysis"]["captionOnlyClaims"][0]["status"] == "not_confirmed_by_vision"
    assert response["damageList"] == []


def test_weighted_median_prefers_better_weighted_near_variant_group():
    vehicle_input = _base_payload()["vehicleInput"] | {"branchId": 2}
    text_analysis = analyze_vehicle_text(vehicle_input)
    listings = []
    for idx, price in enumerate([360000000, 365000000, 370000000, 375000000, 380000000], start=1):
        listings.append(
            {
                "listingId": f"near-{idx}",
                "title": "Toyota Vios G CVT 2021",
                "price": price,
                "categoryId": 1,
                "subcategoryId": 101,
                "year": 2021,
                "mileage": 45000,
                "fuel": "May xang",
                "transmission": "So tu dong",
                "bodyStyle": "Sedan",
                "origin": "Lap rap trong nuoc",
                "branchId": 2,
                "postingDate": "2026-04-10",
            }
        )
    for idx, price in enumerate([450000000, 470000000, 490000000, 500000000, 510000000], start=1):
        listings.append(
            {
                "listingId": f"far-{idx}",
                "title": "Toyota Vios E MT 2024",
                "price": price,
                "categoryId": 1,
                "subcategoryId": 101,
                "year": 2024,
                "mileage": 30000,
                "fuel": "May xang",
                "transmission": "So san",
                "bodyStyle": "Sedan",
                "origin": "Lap rap trong nuoc",
                "branchId": 2,
                "postingDate": "2026-04-10",
            }
        )

    scored = market_statistics.score_and_filter_candidates(vehicle_input, text_analysis, listings)
    stats = market_statistics.build_market_stats(scored, 90, len(listings))

    assert stats["priceStatisticMethod"] == "weighted_median"
    assert stats["weightedMedianPrice"] <= stats["rawMedianPrice"]
    assert stats["weightedMedianNote"] is not None


def _base_payload():
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
            "bodyStyle": "Sedan",
            "origin": "Trong nuoc",
            "description": "Xe tu nhan, khong loi, di gia dinh.",
        },
        "imageAssets": [
            {
                "url": "https://res.cloudinary.com/demo/image/upload/vehicle-pricing/front_001.jpg",
                "publicId": "vehicle-pricing/front_001",
                "source": "cloudinary",
                "declaredGroup": "front",
            },
            {
                "url": "https://res.cloudinary.com/demo/image/upload/vehicle-pricing/duoi_xe.jpg",
                "publicId": "vehicle-pricing/duoi_xe",
                "source": "cloudinary",
                "declaredGroup": "other",
            },
        ],
    }


def _fake_tools(tool_name, params):
    if tool_name == "pricing_validate_reference_data":
        return {
            "valid": True,
            "item": {
                "category_id": 1,
                "subcategory_id": 101,
                "category_name": "Toyota",
                "subcategory_name": "Vios",
            },
        }
    if tool_name == "pricing_get_market_candidates":
        return {
            "items": [
                {
                    "listingId": "1",
                    "vehicleId": 1,
                    "categoryId": 1,
                    "subcategoryId": 101,
                    "title": "Toyota Vios G CVT 2021",
                    "price": 510000000,
                    "year": 2021,
                    "mileage": 45000,
                    "fuel": "May xang",
                    "transmission": "So tu dong",
                    "bodyStyle": "Sedan",
                    "origin": "Lap rap trong nuoc",
                    "branchId": 2,
                    "status": "Available",
                    "postingDate": "2026-04-12",
                },
                {
                    "listingId": "2",
                    "vehicleId": 2,
                    "categoryId": 1,
                    "subcategoryId": 101,
                    "title": "Toyota Vios CVT 2021",
                    "price": 520000000,
                    "year": 2021,
                    "mileage": 47000,
                    "fuel": "May xang",
                    "transmission": "So tu dong",
                    "bodyStyle": "Sedan",
                    "origin": "Lap rap trong nuoc",
                    "branchId": 2,
                    "status": "Available",
                    "postingDate": "2026-04-10",
                },
                {
                    "listingId": "3",
                    "vehicleId": 3,
                    "categoryId": 1,
                    "subcategoryId": 101,
                    "title": "Toyota Vios 2021",
                    "price": 500000000,
                    "year": 2021,
                    "mileage": 43000,
                    "fuel": "May xang",
                    "transmission": "So tu dong",
                    "bodyStyle": "Sedan",
                    "origin": "Lap rap trong nuoc",
                    "branchId": 2,
                    "status": "Available",
                    "postingDate": "2026-04-11",
                },
                {
                    "listingId": "4",
                    "vehicleId": 4,
                    "categoryId": 1,
                    "subcategoryId": 101,
                    "title": "Toyota Vios G CVT 2020",
                    "price": 495000000,
                    "year": 2020,
                    "mileage": 50000,
                    "fuel": "May xang",
                    "transmission": "So tu dong",
                    "bodyStyle": "Sedan",
                    "origin": "Lap rap trong nuoc",
                    "branchId": 2,
                    "status": "Available",
                    "postingDate": "2026-04-09",
                },
                {
                    "listingId": "5",
                    "vehicleId": 5,
                    "categoryId": 1,
                    "subcategoryId": 101,
                    "title": "Toyota Vios E CVT 2021",
                    "price": 490000000,
                    "year": 2021,
                    "mileage": 46000,
                    "fuel": "May xang",
                    "transmission": "So tu dong",
                    "bodyStyle": "Sedan",
                    "origin": "Lap rap trong nuoc",
                    "branchId": 2,
                    "status": "Available",
                    "postingDate": "2026-04-08",
                },
            ],
            "count": 5,
        }
    if tool_name == "pricing_get_segment_candidates":
        return {"items": [], "count": 0}
    raise AssertionError(f"unexpected tool {tool_name}")
