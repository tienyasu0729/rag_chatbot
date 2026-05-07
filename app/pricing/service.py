"""
Orchestration service cho internal pricing flow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.config import get_settings
from app.pricing.condition_aggregation_service import aggregate_condition
from app.pricing.errors import PricingError
from app.pricing.explanation_builder import build_explanation
from app.pricing.guardrail_service import apply_guardrails
from app.pricing.image_analysis_service import validate_and_process_assets
from app.pricing.market_statistics import build_market_stats, score_and_filter_candidates
from app.pricing.mongo_repository import save_valuation
from app.pricing.price_calculator import calculate_prices
from app.pricing.pricing_tools_executor import execute_pricing_tool
from app.pricing.text_analysis_service import analyze_vehicle_text, normalize_text
from app.pricing.vision_inspection_service import inspect_vehicle_images

MIN_GOOD_CANDIDATES = 25
MIN_USABLE_CANDIDATES = 10
MIN_LOW_DATA_CANDIDATES = 5


def estimate_vehicle_price(payload: dict) -> dict:
    vehicle_input = dict(payload["vehicleInput"])
    requested_by = dict(payload["requestedBy"])
    vehicle_input["branchId"] = requested_by.get("branchId")

    processed_images = validate_and_process_assets(payload["imageAssets"])
    initial_text_analysis = analyze_vehicle_text(vehicle_input, candidate_titles=[])
    reference_data = load_reference_data(vehicle_input)
    taxonomy = assess_taxonomy(reference_data.get("item") or {}, initial_text_analysis, vehicle_input)

    try:
        inspection = inspect_vehicle_images(processed_images, vehicle_input)
    except Exception:
        inspection = {
            "inspectionGroups": {},
            "damageFindings": [],
            "riskFlags": [],
            "rawModelOutputs": [],
            "sanitizedInspection": {},
        }

    market_search = collect_market_candidates(vehicle_input, initial_text_analysis, taxonomy)
    similar_titles = [item.get("title") or "" for item in market_search["items"][:10]]
    text_analysis = analyze_vehicle_text(vehicle_input, candidate_titles=similar_titles)

    aggregated = aggregate_condition(
        processed_images=processed_images,
        text_analysis=text_analysis,
        inspection=inspection,
    )
    condition = aggregated["conditionAssessment"]
    risk_assessment = aggregated["riskAssessment"]
    trust_assessment = aggregated["trustAssessment"]
    damage_list = aggregated["damageList"]

    scored = score_and_filter_candidates(vehicle_input, text_analysis, market_search["items"])
    market_stats = build_market_stats(scored, market_search["marketWindowDays"], market_search["rawCount"])
    variant_match_coverage = build_variant_match_coverage(text_analysis, market_stats["filteredListings"])

    fallback = describe_fallback(market_search["fallbackLevel"], market_stats["similarListingsUsed"])
    result_type, result_flags = classify_result(
        market_stats=market_stats,
        market_search=market_search,
        variant_match_coverage=variant_match_coverage,
    )

    prices = calculate_prices(
        vehicle_input,
        condition,
        market_stats,
        fallback_level=fallback["level"],
        variant_confidence=text_analysis["variantConfidence"],
        damage_list=damage_list,
        risk_assessment=risk_assessment,
        trust_assessment=trust_assessment,
        result_type=result_type,
    )
    apply_result_policy(prices, result_type)
    apply_guardrails(
        prices,
        market_stats,
        fallback_level=fallback["level"],
        variant_confidence=text_analysis["variantConfidence"],
        result_type=result_type,
    )

    confidence_breakdown = build_confidence_breakdown(
        market_stats=market_stats,
        text_analysis=text_analysis,
        processed_images=processed_images,
        inspection=inspection,
        variant_match_coverage=variant_match_coverage,
    )
    confidence_policy = apply_confidence_policy(confidence_breakdown, variant_match_coverage)
    confidence_breakdown = confidence_policy["breakdown"]
    confidence = confidence_policy["confidence"]
    confidence_label = confidence_policy["label"]
    confidence_warnings = confidence_policy["warnings"]
    caption_analysis = build_image_caption_analysis(processed_images, inspection)
    if caption_analysis.get("captionConflicts"):
        trust_assessment.setdefault("trustFlags", []).append(
            {
                "type": "caption_vision_conflict",
                "severity": "low",
                "message": "Có ghi chú ảnh của người dùng chưa được xác nhận rõ bằng vision, cần đối chiếu thực tế.",
            }
        )

    business_warnings, internal_diagnostics, warnings = build_warning_sets(
        condition=condition,
        risk_assessment=risk_assessment,
        trust_assessment=trust_assessment,
        taxonomy=taxonomy,
        text_analysis=text_analysis,
        market_stats=market_stats,
        variant_match_coverage=variant_match_coverage,
        result_type=result_type,
        processed_images=processed_images,
        market_search=market_search,
        confidence_warnings=confidence_warnings,
    )
    prices["dealSuggestion"]["talkingPoints"] = build_deal_talking_points(
        business_warnings=business_warnings,
        damage_list=damage_list,
        variant_match_coverage=variant_match_coverage,
        market_data_confidence=confidence_breakdown["marketDataConfidence"],
    )

    expert_explanation = build_explanation(
        market_stats=market_stats,
        pricing_breakdown=prices["pricingBreakdown"],
        condition=condition,
        risk_assessment=risk_assessment,
        trust_assessment=trust_assessment,
        pricing_adjustments=prices["pricingAdjustments"],
        warnings=business_warnings,
        fallback=fallback,
        result_type=result_type,
        variant_match_coverage=variant_match_coverage,
    )

    data_basis = {
        "source": "oto.com.vn",
        "type": "market_listing_price",
        "note": "Giá được tính từ dữ liệu rao bán xe cũ trên thị trường, không phải giá thu vào hoặc giá chốt sau thương lượng.",
    }
    vehicle_understanding = {
        "detectedBrand": text_analysis["detectedBrand"],
        "detectedModel": text_analysis["detectedModel"],
        "brandKeyword": text_analysis["brandKeyword"],
        "modelKeyword": text_analysis["modelKeyword"],
        "detectedVariant": text_analysis["detectedVariant"],
        "variantConfidence": text_analysis["variantConfidence"],
        "normalizedFuel": text_analysis["normalizedFuel"],
        "normalizedTransmission": text_analysis["normalizedTransmission"],
        "taxonomyMismatch": taxonomy["taxonomyMismatch"],
        "taxonomyWarning": taxonomy["taxonomyWarning"],
        "warning": build_vehicle_understanding_warning(result_type, variant_match_coverage),
    }

    valuation_id = build_valuation_id()
    market_search_payload = {
        "toolName": market_search.get("toolName", "pricing_get_market_candidates"),
        "marketWindowDays": market_search.get("marketWindowDays", 90),
        "fallbackWindowUsed": market_search.get("fallbackLevel", 1) > 1,
        "fallbackLevel": market_search.get("fallbackLevel", 1),
        "inputCategoryId": vehicle_input["categoryId"],
        "inputSubcategoryId": vehicle_input["subcategoryId"],
        "inputCategoryName": taxonomy.get("inputCategoryName"),
        "inputSubcategoryName": taxonomy.get("inputSubcategoryName"),
        "selectedAttemptLevel": market_search.get("selectedAttemptLevel", market_search.get("fallbackLevel", 1)),
        "finalSampleSize": market_stats["usedForPricingCount"],
        "effectiveSampleSize": market_stats["effectiveSampleSize"],
        "totalWeight": market_stats["totalWeight"],
        "fallbackReason": market_search.get("fallbackReason"),
        "marketWindow": market_search.get(
            "marketWindow",
            {
                "initialDays": 90,
                "usedDays": market_search.get("marketWindowDays", 90),
                "fallbackWindowUsed": market_search.get("marketWindowDays", 90) > 90,
                "reason": market_search.get("fallbackReason"),
            },
        ),
        "rawCount": market_search.get("rawCount", market_search.get("count", 0)),
        "scoredCount": market_stats["scoredCount"],
        "eligibleCount": market_stats["eligibleCount"],
        "usedCount": market_stats["usedForPricingCount"],
        "outliersRemoved": market_stats["outliersRemoved"],
        "attempts": market_search.get("attempts", []),
        "diagnostics": market_search.get("diagnostics", []),
        "similarListingsFound": market_stats["similarListingsFound"],
        "similarListingsUsed": market_stats["similarListingsUsed"],
    }
    image_processing_payload = {
        "uploadedCount": processed_images["uploadedCount"],
        "validImageCount": processed_images["validImageCount"],
        "exactDuplicatesRemoved": processed_images["exactDuplicatesRemoved"],
        "nearDuplicatesRemoved": processed_images["nearDuplicatesRemoved"],
        "analyzedCount": processed_images["analyzedCount"],
        "groups": processed_images["groups"],
        "coveredViews": processed_images["coveredViews"],
        "partialViews": processed_images["partialViews"],
        "missingViews": processed_images["missingViews"],
        "incompleteViews": processed_images["incompleteViews"],
        "inspectionGroups": processed_images["inspectionGroups"],
        "ignoredImages": processed_images["ignoredImages"],
    }
    top_comparables = build_response_comparables(market_stats["filteredListings"], limit=10)

    response = {
        "valuationId": valuation_id,
        "resultType": result_type,
        "resultFlags": result_flags,
        "dataBasis": data_basis,
        "vehicleUnderstanding": vehicle_understanding,
        "marketReferencePrice": prices["marketReferencePrice"],
        "fairPrice": prices["fairPrice"],
        "dealSuggestion": prices["dealSuggestion"],
        "marketSellingPrice": prices["marketSellingPrice"],
        "purchasePrice": prices["purchasePrice"],
        "roughPurchaseRange": prices.get("roughPurchaseRange"),
        "pricingBreakdown": prices["pricingBreakdown"],
        "conditionAssessment": condition,
        "riskAssessment": risk_assessment,
        "trustAssessment": trust_assessment,
        "imageProcessing": image_processing_payload,
        "damageList": damage_list,
        "pricingAdjustments": prices["pricingAdjustments"],
        "topComparablesUsed": top_comparables,
        "marketSearch": market_search_payload,
        "marketStats": {
            "similarListingsFound": market_stats["similarListingsFound"],
            "similarListingsUsed": market_stats["similarListingsUsed"],
            "sampleSize": market_stats["sampleSize"],
            "effectiveSampleSize": market_stats["effectiveSampleSize"],
            "totalWeight": market_stats["totalWeight"],
            "statisticalStrength": market_stats["statisticalStrength"],
            "observedMinPrice": market_stats["observedMinPrice"],
            "observedMaxPrice": market_stats["observedMaxPrice"],
            "outliersRemoved": market_stats["outliersRemoved"],
            "medianPrice": market_stats["medianPrice"],
            "p25Price": market_stats["p25Price"],
            "p75Price": market_stats["p75Price"],
            "weightedMedianPrice": market_stats["weightedMedianPrice"],
            "weightedP25Price": market_stats["weightedP25Price"],
            "weightedP75Price": market_stats["weightedP75Price"],
            "priceStatisticMethod": market_stats["priceStatisticMethod"],
            "rawMedianPrice": market_stats["rawMedianPrice"],
            "weightedMedianNote": market_stats["weightedMedianNote"],
            "averageSimilarityScore": market_stats["averageSimilarityScore"],
            "note": market_stats["note"],
            "marketWindowDays": market_stats["marketWindowDays"],
        },
        "fallback": fallback,
        "confidence": confidence,
        "confidenceLabel": confidence_label,
        "confidenceWarnings": confidence_warnings,
        "confidenceBreakdown": confidence_breakdown,
        "variantMatchCoverage": variant_match_coverage,
        "imageCaptionAnalysis": caption_analysis,
        "businessWarnings": business_warnings,
        "internalDiagnostics": internal_diagnostics,
        "warnings": warnings,
        "expertExplanation": expert_explanation,
    }

    persist_document = {
        "_id": valuation_id,
        "schemaVersion": get_settings().PRICING_SCHEMA_VERSION,
        "source": "java_spring_backend",
        "status": "completed",
        "requestId": payload["requestId"],
        "requestedBy": requested_by,
        "input": {
            "vehicleInput": vehicle_input,
            "imageAssets": payload["imageAssets"],
        },
        "dataBasis": data_basis,
        "textAnalysis": text_analysis,
        "imageProcessing": image_processing_payload,
        "imageAnalysis": {
            "rawModelOutputs": inspection.get("rawModelOutputs", []),
            "sanitizedInspection": inspection.get("sanitizedInspection", {}),
            "imageCaptionAnalysis": caption_analysis,
        },
        "inspection": {
            "carQualityScore": condition["carQualityScore"],
            "riskScore": risk_assessment["riskScore"],
            "trustScore": trust_assessment["trustScore"],
            "exteriorScore": condition.get("exteriorScore"),
            "interiorScore": condition.get("interiorScore"),
            "engineBayScore": condition.get("engineBayScore"),
            "damageList": damage_list,
            "trustFlags": trust_assessment["trustFlags"],
        },
        "marketSearch": market_search_payload,
        "marketStats": response["marketStats"],
        "pricingBreakdown": prices["pricingBreakdown"],
        "pricingAdjustments": prices["pricingAdjustments"],
        "fairPrice": prices["fairPrice"],
        "dealSuggestion": prices["dealSuggestion"],
        "topComparablesUsed": top_comparables,
        "fullComparablesUsed": market_stats["allCandidates"],
        "result": {
            "resultType": result_type,
            "resultFlags": result_flags,
            "marketReferencePrice": prices["marketReferencePrice"],
            "marketSellingPrice": prices["marketSellingPrice"],
            "fairPrice": prices["fairPrice"],
            "purchasePrice": prices["purchasePrice"],
            "roughPurchaseRange": prices.get("roughPurchaseRange"),
            "dealSuggestion": prices["dealSuggestion"],
            "confidence": confidence,
            "confidenceLabel": confidence_label,
            "confidenceWarnings": confidence_warnings,
            "confidenceBreakdown": confidence_breakdown,
            "variantMatchCoverage": variant_match_coverage,
        },
        "businessWarnings": business_warnings,
        "internalDiagnostics": internal_diagnostics,
        "allWarningsForAudit": warnings,
        "expertExplanation": expert_explanation,
        "warnings": warnings,
        "aiUsage": {
            "visionModel": get_settings().VISION_MODEL or "rule_based_fallback",
            "textModel": None,
            "promptVersion": get_settings().PRICING_SCHEMA_VERSION,
            "latencyMs": None,
        },
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    save_valuation(persist_document)
    return response


def load_reference_data(vehicle_input: dict) -> dict:
    try:
        reference_data = execute_pricing_tool(
            "pricing_validate_reference_data",
            {
                "category_id": vehicle_input["categoryId"],
                "subcategory_id": vehicle_input["subcategoryId"],
            },
        )
    except PricingError:
        raise
    except Exception as exc:
        raise PricingError("market_data_unavailable", "Khong kiem tra duoc reference data tu SQL Server", status_code=503) from exc
    if not reference_data.get("valid"):
        raise PricingError("invalid_request", "categoryId/subcategoryId khong hop le", status_code=422)
    return reference_data


def assess_taxonomy(reference_item: dict, text_analysis: dict, vehicle_input: dict) -> dict:
    subcategory_name = str(reference_item.get("subcategory_name") or reference_item.get("subcategoryName") or "")
    category_name = str(reference_item.get("category_name") or reference_item.get("categoryName") or "")
    model_keyword = normalize_text(str(text_analysis.get("modelKeyword") or ""))
    normalized_subcategory = normalize_text(subcategory_name)
    taxonomy_mismatch = bool(model_keyword and normalized_subcategory and model_keyword not in normalized_subcategory)
    taxonomy_warning = None
    if taxonomy_mismatch:
        detected = " ".join(part for part in [text_analysis.get("detectedBrand"), text_analysis.get("detectedModel")] if part)
        taxonomy_warning = f"Title co ve la {detected or model_keyword} nhung subcategoryId hien tai co the khong khop du lieu thi truong."
    return {
        "taxonomyMismatch": taxonomy_mismatch,
        "taxonomyWarning": taxonomy_warning,
        "inputCategoryName": category_name or None,
        "inputSubcategoryName": subcategory_name or None,
    }


def collect_market_candidates(vehicle_input: dict, text_analysis: dict, taxonomy: dict) -> dict:
    model_keyword = text_analysis.get("modelKeyword")
    attempts = []
    diagnostics = []
    all_candidates = []
    seen_listing_ids = set()
    selected_result = None
    fallback_reason = None
    selected_attempt_level = None
    selected_window_days = 90

    strategies = [
        {
            "level": 1,
            "description": "Same subcategory, same model, year ±1, 90 days",
            "toolName": "pricing_get_market_candidates",
            "params": {
                "limit": 180,
                "category_id": vehicle_input["categoryId"],
                "subcategory_id": vehicle_input["subcategoryId"],
                "year": vehicle_input.get("year"),
                "year_range": 1,
                "model_keyword": model_keyword or None,
                "market_window_days": 90,
            },
            "usesSubcategory": True,
        },
        {
            "level": 2,
            "description": "Same subcategory, same model, year ±2, 180 days",
            "toolName": "pricing_get_market_candidates",
            "params": {
                "limit": 240,
                "category_id": vehicle_input["categoryId"],
                "subcategory_id": vehicle_input["subcategoryId"],
                "year": vehicle_input.get("year"),
                "year_range": 2,
                "model_keyword": model_keyword or None,
                "market_window_days": 180,
            },
            "usesSubcategory": True,
        },
        {
            "level": 3,
            "description": "Category + model keyword, year ±3, 365 days, ignore subcategory",
            "toolName": "pricing_get_market_candidates",
            "params": {
                "limit": 320,
                "category_id": vehicle_input["categoryId"],
                "subcategory_id": None,
                "year": vehicle_input.get("year"),
                "year_range": 3,
                "model_keyword": model_keyword or None,
                "market_window_days": 365,
            },
            "usesSubcategory": False,
        },
        {
            "level": 4,
            "description": "Category + model keyword, year ±4, 720 days, ignore subcategory",
            "toolName": "pricing_get_market_candidates",
            "params": {
                "limit": 500,
                "category_id": vehicle_input["categoryId"],
                "subcategory_id": None,
                "year": vehicle_input.get("year"),
                "year_range": 4,
                "model_keyword": model_keyword or None,
                "market_window_days": 720,
            },
            "usesSubcategory": False,
        },
        {
            "level": 5,
            "description": "Segment fallback by body style",
            "toolName": "pricing_get_segment_candidates",
            "params": {
                "limit": 300,
                "category_id": vehicle_input["categoryId"],
                "body_style": vehicle_input.get("bodyStyle"),
                "year": vehicle_input.get("year"),
                "year_range": 4,
                "market_window_days": 720,
            },
            "usesSubcategory": False,
        },
    ]

    for strategy in strategies:
        if strategy["level"] == 5 and selected_result and selected_result["usedForPricingCount"] >= MIN_LOW_DATA_CANDIDATES:
            break

        try:
            result = execute_pricing_tool(strategy["toolName"], strategy["params"])
        except PricingError:
            raise
        except Exception as exc:
            raise PricingError("market_data_unavailable", "Khong lay duoc market candidates tu SQL Server", status_code=503) from exc

        for item in result.get("items", []):
            listing_id = str(item.get("listingId") or "")
            if listing_id and listing_id in seen_listing_ids:
                continue
            if listing_id:
                seen_listing_ids.add(listing_id)
            all_candidates.append(item)

        scored = score_and_filter_candidates(vehicle_input, text_analysis, all_candidates)
        stats = build_market_stats(scored, strategy["params"]["market_window_days"], len(all_candidates))
        attempt = {
            "level": strategy["level"],
            "description": strategy["description"],
            "toolName": strategy["toolName"],
            "paramsUsed": dict(strategy["params"]),
            "rawCount": int(result.get("count", 0)),
            "scoredCount": stats["scoredCount"],
            "eligibleCount": stats["eligibleCount"],
            "usedForPricingCount": stats["usedForPricingCount"],
        }
        attempts.append(attempt)
        selected_result = stats
        selected_attempt_level = strategy["level"]
        selected_window_days = strategy["params"]["market_window_days"]

        if not strategy["usesSubcategory"]:
            diagnostics.append("Da bo subcategory de mo rong market query theo model keyword.")
        if strategy["params"]["market_window_days"] > 90:
            diagnostics.append("Da mo rong market window de tang do on dinh thong ke.")
        if strategy["level"] == 5:
            diagnostics.append("Da fallback sang segment/body style vi model fallback van thieu du lieu.")

        if stats["usedForPricingCount"] >= MIN_GOOD_CANDIDATES:
            fallback_reason = f"Da dat nguong mau tot o level {strategy['level']}."
            break
        if strategy["level"] == 4 and stats["usedForPricingCount"] >= MIN_LOW_DATA_CANDIDATES:
            fallback_reason = "Level 4 da dat nguong toi thieu de dinh gia theo model fallback."
            break
        if strategy["level"] == 5:
            fallback_reason = "Model fallback van thieu du lieu, da dung segment fallback."

    if not selected_result:
        selected_result = build_market_stats({"candidates": [], "scoredCount": 0, "eligibleCount": 0, "usedForPricingCount": 0}, 90, 0)
        selected_attempt_level = 5
        selected_window_days = 90
        fallback_reason = "Khong tim thay candidate phu hop."

    if not fallback_reason:
        fallback_reason = f"Level 1 chi co {selected_result['usedForPricingCount']} comparable dung duoc, da dung ket qua mo rong hien co."

    return {
        "items": all_candidates,
        "count": len(all_candidates),
        "rawCount": len(all_candidates),
        "fallbackLevel": selected_attempt_level,
        "selectedAttemptLevel": selected_attempt_level,
        "marketWindowDays": selected_window_days,
        "marketWindow": {
            "initialDays": 90,
            "usedDays": selected_window_days,
            "fallbackWindowUsed": selected_window_days > 90,
            "reason": fallback_reason,
        },
        "toolName": "pricing_get_segment_candidates" if selected_attempt_level == 5 else "pricing_get_market_candidates",
        "attempts": attempts,
        "diagnostics": list(dict.fromkeys(diagnostics)),
        "taxonomyFallbackUsed": selected_attempt_level in {3, 4},
        "taxonomyMismatch": bool(taxonomy.get("taxonomyMismatch")),
        "fallbackReason": fallback_reason,
    }


def classify_result(*, market_stats: dict, market_search: dict, variant_match_coverage: dict) -> tuple[str, list[str]]:
    flags = []
    used_count = int(market_stats.get("usedForPricingCount") or 0)
    effective_sample = float(market_stats.get("effectiveSampleSize") or 0)
    avg_similarity = float(market_stats.get("averageSimilarityScore") or 0)
    selected_level = int(market_search.get("selectedAttemptLevel") or market_search.get("fallbackLevel") or 1)
    if market_search.get("toolName") == "pricing_get_segment_candidates" and selected_level < 5:
        selected_level = 5
    candidate_variant_confidence = float(variant_match_coverage.get("candidateVariantConfidence") or 0)
    exact_variant_matches = int(variant_match_coverage.get("exactVariantMatches") or 0)

    if selected_level >= 3:
        flags.append("subcategory_broadened")
    if market_search.get("marketWindow", {}).get("usedDays", 90) > 90:
        flags.append("market_window_broadened")
    if market_search.get("taxonomyMismatch"):
        flags.append("taxonomy_mismatch_warning")
    if used_count < 5:
        flags.append("low_market_data")
    if exact_variant_matches == 0:
        flags.append("variant_uncertain")
    if selected_level == 5:
        flags.append("segment_fallback")

    if used_count < 1:
        return "insufficient_market_data", unique_list(flags)
    if selected_level == 5:
        return "rough_segment_estimate", unique_list(flags)
    if used_count < 5 or effective_sample < 5:
        return "low_data_model_estimate", unique_list(flags)
    if exact_variant_matches == 0 or candidate_variant_confidence < 0.45 or avg_similarity < 72:
        return "variant_uncertain_estimate", unique_list(flags)
    if used_count >= MIN_USABLE_CANDIDATES and effective_sample >= 6 and avg_similarity >= 75 and candidate_variant_confidence >= 0.55 and selected_level <= 4:
        return "standard_estimate", unique_list(flags)
    return "variant_uncertain_estimate", unique_list(flags)


def describe_fallback(level: int, similar_used: int) -> dict:
    descriptions = {
        1: "Co du lieu cung model trong cua so tim kiem hep.",
        2: "Da mo rong year range va market window de tang mau.",
        3: "Da bo subcategory va giu model keyword de mo rong du lieu cung model.",
        4: "Da mo rong model fallback toi muc recency/life-window rong hon.",
        5: "Da fallback sang segment/body style vi model fallback van thieu du lieu.",
    }
    return {
        "level": level,
        "used": level > 1 or similar_used < 10,
        "description": descriptions[level],
    }


def apply_result_policy(prices: dict, result_type: str) -> None:
    if result_type == "rough_segment_estimate":
        prices["purchasePrice"]["suggestedPrice"] = None
        prices["purchasePrice"]["minPrice"] = None
        prices["purchasePrice"]["maxPrice"] = None
        prices["dealSuggestion"]["recommendedOfferPrice"] = None
        prices["dealSuggestion"]["targetPurchasePrice"] = None
        prices["dealSuggestion"]["maxAcceptablePurchasePrice"] = None
        prices["dealSuggestion"]["negotiationRange"] = {"start": None, "target": None, "ceiling": None}
    elif result_type == "insufficient_market_data":
        prices["marketSellingPrice"]["suggestedPrice"] = None
        prices["marketSellingPrice"]["minPrice"] = None
        prices["marketSellingPrice"]["maxPrice"] = None
        prices["marketReferencePrice"]["median"] = None
        prices["marketReferencePrice"]["range"]["min"] = None
        prices["marketReferencePrice"]["range"]["max"] = None
        prices["fairPrice"]["suggestedPrice"] = None
        prices["fairPrice"]["range"] = {"min": None, "max": None}
        prices["purchasePrice"]["suggestedPrice"] = None
        prices["purchasePrice"]["minPrice"] = None
        prices["purchasePrice"]["maxPrice"] = None
        prices["dealSuggestion"]["recommendedOfferPrice"] = None
        prices["dealSuggestion"]["targetPurchasePrice"] = None
        prices["dealSuggestion"]["maxAcceptablePurchasePrice"] = None
        prices["dealSuggestion"]["negotiationRange"] = {"start": None, "target": None, "ceiling": None}
        prices["roughPurchaseRange"] = None


def build_confidence_breakdown(*, market_stats: dict, text_analysis: dict, processed_images: dict, inspection: dict, variant_match_coverage: dict) -> dict:
    used_count = int(market_stats.get("usedForPricingCount") or 0)
    effective_sample = float(market_stats.get("effectiveSampleSize") or 0)
    if used_count >= 25 and effective_sample >= 10:
        market_confidence = 0.85
    elif used_count >= 10 and effective_sample >= 6:
        market_confidence = 0.68
    elif used_count >= 5:
        market_confidence = 0.48
    elif used_count >= 1:
        market_confidence = 0.3
    else:
        market_confidence = 0.1

    variant_confidence = round(
        min(
            0.95,
            max(
                0.15,
                (float(text_analysis.get("variantConfidence") or 0) + float(variant_match_coverage.get("candidateVariantConfidence") or 0)) / 2,
            ),
        ),
        2,
    )
    full_views = len(processed_images.get("coveredViews", []))
    partial_views = len(processed_images.get("partialViews", []))
    missing_views = len(processed_images.get("missingViews", []))
    image_coverage_confidence = round(max(0.2, min(0.95, 0.4 + full_views * 0.05 + partial_views * 0.02 - missing_views * 0.05)), 2)
    inspection_groups = inspection.get("inspectionGroups", {})
    if inspection_groups:
        confidences = [float(group.get("confidence") or 0.55) for group in inspection_groups.values()]
        vision_confidence = round(sum(confidences) / len(confidences), 2)
    else:
        vision_confidence = 0.45

    overall = round(
        max(
            0.15,
            min(
                0.92,
                market_confidence * 0.4 + variant_confidence * 0.25 + image_coverage_confidence * 0.2 + vision_confidence * 0.15,
            ),
        ),
        2,
    )
    return {
        "marketDataConfidence": market_confidence,
        "variantMatchConfidence": variant_confidence,
        "imageCoverageConfidence": image_coverage_confidence,
        "visionConfidence": vision_confidence,
        "overallConfidence": overall,
    }


def apply_confidence_policy(confidence_breakdown: dict, variant_match_coverage: dict) -> dict:
    breakdown = dict(confidence_breakdown)
    warnings = []
    confidence = float(breakdown.get("overallConfidence") or 0)
    exact_matches = int(variant_match_coverage.get("exactVariantMatches") or 0)
    partial_matches = int(variant_match_coverage.get("partialVariantMatches") or 0)
    different_matches = int(variant_match_coverage.get("differentVariantMatches") or 0)
    candidate_variant_confidence = float(variant_match_coverage.get("candidateVariantConfidence") or 0)

    if exact_matches == 0:
        confidence = min(confidence, 0.62)
        warnings.append("Chưa có đủ tin rao khớp chính xác phiên bản xe input.")
        if different_matches >= partial_matches:
            confidence = min(confidence, 0.60)
        warnings.append("Giá đang được suy luận từ xe cùng dòng hoặc gần phiên bản.")

    breakdown["overallConfidence"] = round(confidence, 2)
    label = confidence_label_from_score(confidence)
    if candidate_variant_confidence < 0.4 and label in {"Trung binh", "Cao"}:
        label = "Trung binh thap"
    return {
        "breakdown": breakdown,
        "confidence": round(confidence, 2),
        "label": label,
        "warnings": unique_list(warnings),
    }


def build_variant_match_coverage(text_analysis: dict, filtered_listings: list[dict]) -> dict:
    input_variant = normalize_text(str(text_analysis.get("detectedVariant") or ""))
    exact = 0
    partial = 0
    unknown = 0
    different = 0

    for item in filtered_listings:
        variant_match = str(item.get("variantMatch") or "unknown")
        if variant_match == "exact":
            exact += 1
        elif variant_match == "partial":
            partial += 1
        elif variant_match == "different_variant":
            different += 1
        else:
            unknown += 1

    total = len(filtered_listings)
    confidence = 0.0
    if total:
        confidence = round(min(0.95, (exact * 1.0 + partial * 0.7 + unknown * 0.35 + different * 0.15) / total), 2)
    return {
        "inputVariant": text_analysis.get("detectedVariant") or input_variant or None,
        "exactVariantMatches": exact,
        "partialVariantMatches": partial,
        "unknownVariantMatches": unknown,
        "differentVariantMatches": different,
        "candidateVariantConfidence": confidence,
    }


def build_warning_sets(
    *,
    condition: dict,
    risk_assessment: dict,
    trust_assessment: dict,
    taxonomy: dict,
    text_analysis: dict,
    market_stats: dict,
    variant_match_coverage: dict,
    result_type: str,
    processed_images: dict,
    market_search: dict,
    confidence_warnings: list[str],
) -> tuple[list[str], list[str], list[str]]:
    business = []
    internal = list(market_search.get("diagnostics", []))

    business.extend(condition.get("warnings", []))
    for flag in risk_assessment.get("riskFlags", []):
        if flag.get("message"):
            business.append(flag["message"])
    for flag in trust_assessment.get("trustFlags", []):
        flag_type = str(flag.get("type") or "")
        message = str(flag.get("message") or "")
        if flag_type in {"group_mismatch_resolved", "document_image_not_used_for_condition"}:
            if message:
                internal.append(message)
        elif message:
            business.append(message)

    business.extend(text_analysis.get("inputConflicts", []))
    if taxonomy["taxonomyWarning"]:
        business.append(taxonomy["taxonomyWarning"])
    business.extend(confidence_warnings)
    used_count = int(market_stats.get("usedForPricingCount") or 0)
    if used_count and used_count < 5:
        business.append(f"Chỉ có {used_count} xe tham chiếu dùng được, giá chỉ nên dùng để tham khảo.")
    if variant_match_coverage.get("exactVariantMatches", 0) == 0 and used_count > 0:
        business.append("Chưa có đủ dữ liệu đúng phiên bản; giá được suy luận từ xe cùng dòng hoặc gần phiên bản.")
    if result_type == "rough_segment_estimate":
        business.append("Kết quả chỉ là tham chiếu theo nhóm xe gần tương đồng, không phải giá thu vào chắc chắn.")
    business.append("Giá dựa trên giá rao bán thị trường, không phải giá chốt giao dịch.")

    return unique_list([item for item in business if item]), unique_list([item for item in internal if item]), unique_list([item for item in business + internal if item])


def build_deal_talking_points(*, business_warnings: list[str], damage_list: list[dict], variant_match_coverage: dict, market_data_confidence: float) -> list[str]:
    points = []
    point_types: list[str] = []
    for item in damage_list:
        label = str(item.get("label") or "").strip()
        if label:
            point_types.append(f"damage:{label}")
            points.append(f"{label} cần được trừ giá khi thương lượng.")
    for warning in business_warnings:
        warning_type, message = map_business_warning(warning)
        if warning_type and warning_type not in point_types:
            point_types.append(warning_type)
            points.append(message)
    if variant_match_coverage.get("exactVariantMatches", 0) == 0:
        if "variant_uncertain" not in point_types:
            point_types.append("variant_uncertain")
            points.append("Dữ liệu thị trường chưa có đủ xe đúng phiên bản, nên cần giữ biên an toàn khi deal.")
    if market_data_confidence < 0.5 and "low_market_confidence" not in point_types:
        points.append("Dữ liệu thị trường chưa mạnh, nên giữ biên đàm phán thận trọng hơn.")
    return unique_list(points[:5]) or ["Xe cần kiểm tra thực tế thêm trước khi chốt giá cuối."]


def build_response_comparables(candidates: list[dict], *, limit: int) -> list[dict]:
    response_items = []
    for item in candidates[:limit]:
        response_items.append(
            {
                "listingId": item.get("listingId"),
                "title": item.get("title"),
                "price": item.get("price"),
                "year": item.get("year"),
                "mileage": item.get("mileage"),
                "transmission": item.get("transmission"),
                "fuel": item.get("fuel"),
                "variantDetected": item.get("variantDetected"),
                "variantMatch": item.get("variantMatch"),
                "similarityScore": item.get("similarityScore"),
                "weight": item.get("weight"),
                "usedForPricing": item.get("usedForPricing"),
                "warnings": item.get("warnings", []),
                "dataQualityFlags": item.get("dataQualityFlags", []),
                "weightAdjustmentReasons": item.get("weightAdjustmentReasons", []),
                "excludedReason": item.get("excludedReason"),
            }
        )
    return response_items


def build_vehicle_understanding_warning(result_type: str, variant_match_coverage: dict) -> str | None:
    if result_type == "rough_segment_estimate":
        return "Dữ liệu cùng model không đủ mạnh, kết quả đang fallback theo segment."
    if result_type == "low_data_model_estimate":
        return "Số xe tham chiếu cùng model còn ít, kết quả chỉ nên dùng để tham khảo."
    if variant_match_coverage.get("exactVariantMatches", 0) == 0:
        return "Chưa có đủ dữ liệu đúng phiên bản, giá có thể dao động rộng hơn."
    return None


def confidence_label_from_score(score: float) -> str:
    if score >= 0.8:
        return "Cao"
    if score >= 0.6:
        return "Trung binh"
    if score >= 0.5:
        return "Trung binh thap"
    if score >= 0.4:
        return "Thap"
    return "Rat thap"


def build_image_caption_analysis(processed_images: dict, inspection: dict) -> dict:
    accepted_assets = processed_images.get("acceptedAssets", [])
    caption_assets = [asset for asset in accepted_assets if getattr(asset, "caption", None)]
    help_resolve = 0
    confirmed = 0
    conflicts = 0
    caption_only_claims = []
    findings_by_group = inspection.get("inspectionGroups", {})

    for asset in caption_assets:
        if getattr(asset, "caption_hint_group", "other") != "other" and asset.declared_group == "other":
            help_resolve += 1
        asset_findings = (findings_by_group.get(asset.inspection_group or "", {}) or {}).get("findings", [])
        if asset.caption_claims:
            matched = False
            for claim in asset.caption_claims:
                issue = str(claim.get("issue") or "")
                if any(str(item.get("issue") or "") == issue for item in asset_findings):
                    matched = True
                    confirmed += 1
                else:
                    caption_only_claims.append(
                        {
                            "publicId": asset.public_id,
                            "claim": claim.get("text") or asset.caption,
                            "status": "not_confirmed_by_vision",
                        }
                    )
            if not matched:
                conflicts += 1

    return {
        "captionProvidedCount": len(caption_assets),
        "captionHelpedResolveGroups": help_resolve,
        "captionConfirmedFindings": confirmed,
        "captionConflicts": conflicts,
        "captionOnlyClaims": caption_only_claims,
    }


def map_business_warning(warning: str) -> tuple[str | None, str]:
    lowered = warning.lower()
    if "engine_bay" in lowered or "khoang may" in lowered:
        return "missing_engine_bay", "Chưa có ảnh khoang máy nên chưa đánh giá được tình trạng máy trực quan."
    if "odometer" in lowered or "odo" in lowered:
        return "missing_odometer", "Chưa có ảnh đồng hồ ODO nên chưa đối chiếu được số km khai báo."
    if "exact variant" in lowered or "phien ban" in lowered:
        return "variant_uncertain", "Dữ liệu thị trường chưa có đủ xe đúng phiên bản, nên cần giữ biên an toàn khi deal."
    if "tham khao" in lowered and "segment" not in lowered:
        return "reference_only", "Giá hiện tại nên được xem như mức tham khảo để đàm phán."
    return None, warning


def unique_list(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def build_valuation_id() -> str:
    now = datetime.now(timezone.utc)
    return f"val_{now.strftime('%Y%m%d')}_{uuid4().hex[:8]}"
