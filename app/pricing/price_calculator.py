"""
Tính market reference, fair price và deal suggestion.
"""

from __future__ import annotations

from typing import Any


LUXURY_BRANDS = {"mercedes", "bmw", "audi", "lexus", "porsche", "land rover", "volvo"}


def calculate_prices(
    vehicle_input: dict[str, Any],
    condition: dict[str, Any],
    market_stats: dict[str, Any],
    *,
    fallback_level: int,
    variant_confidence: float,
    damage_list: list[dict[str, Any]] | None = None,
    risk_assessment: dict[str, Any] | None = None,
    trust_assessment: dict[str, Any] | None = None,
    result_type: str | None = None,
) -> dict[str, Any]:
    damage_list = damage_list or []
    risk_assessment = risk_assessment or {}
    trust_assessment = trust_assessment or {}

    median_price = market_stats.get("medianPrice")
    p25 = market_stats.get("p25Price")
    p75 = market_stats.get("p75Price")
    if not median_price:
        return {
            "marketReferencePrice": {"median": None, "range": {"min": p25, "max": p75}, "label": "Giá rao bán thị trường tham khảo"},
            "fairPrice": {"rawSuggestedPrice": None, "suggestedPrice": None, "range": {"min": None, "max": None}, "label": "Giá hợp lý sau khi xét condition và trust", "roundingStep": None, "roundingNote": None},
            "dealSuggestion": {"recommendedOfferPrice": None, "targetPurchasePrice": None, "maxAcceptablePurchasePrice": None, "negotiationRange": {"start": None, "target": None, "ceiling": None}, "label": "Gợi ý mức mua/deal", "talkingPoints": []},
            "marketSellingPrice": {"suggestedPrice": None, "minPrice": p25, "maxPrice": p75, "label": "Giá bán ra thị trường tham khảo"},
            "purchasePrice": {"suggestedPrice": None, "minPrice": None, "maxPrice": None, "label": "Giá thu vào đề xuất"},
            "roughPurchaseRange": None,
            "pricingBreakdown": {"marketMedianPrice": None, "conditionAdjustment": 0, "visualAdjustment": 0, "trustAdjustment": 0, "baseReconditioningCost": 0, "damageRepairCost": 0, "estimatedReconditioningCost": 0, "riskBuffer": 0, "targetMargin": 0, "roundingStep": None},
            "pricingAdjustments": [],
        }

    market_reference_price = int(median_price)
    condition_discount = int(round(market_reference_price * condition_discount_rate(condition)))
    trust_penalty = compute_trust_penalty(market_reference_price, trust_assessment)
    fair_price_raw = max(0, market_reference_price - condition_discount - trust_penalty)

    base_reconditioning_cost = compute_base_reconditioning_cost(market_reference_price)
    damage_repair_cost, damage_adjustments = build_reconditioning_adjustments(market_reference_price, damage_list, condition)
    recon_cost = base_reconditioning_cost + damage_repair_cost
    risk_buffer = int(round(fair_price_raw * risk_buffer_rate(condition, fallback_level, variant_confidence, risk_assessment)))
    target_margin = int(round(fair_price_raw * target_margin_rate(vehicle_input)))
    purchase_price_raw = max(0, fair_price_raw - recon_cost - risk_buffer - target_margin)

    spread_rate = 0.08 if result_type == "low_data_model_estimate" else 0.04
    price_range_padding = max(10_000_000 if result_type == "low_data_model_estimate" else 5_000_000, int(round(market_reference_price * spread_rate)))
    recommended_offer_raw = max(0, purchase_price_raw - int(round(market_reference_price * 0.02)))
    target_purchase_raw = purchase_price_raw
    max_purchase_raw = max(0, fair_price_raw - target_margin)
    rounding_step = price_rounding_step(market_reference_price)
    rounding_note = f"Giá hiển thị đã được làm tròn theo bậc {rounding_step:,} VND.".replace(",", ".")

    fair_price = round_to_step(fair_price_raw, rounding_step)
    fair_min = round_to_step(max(0, fair_price - price_range_padding), rounding_step)
    fair_max = round_to_step(fair_price + price_range_padding, rounding_step)
    market_reference_price = round_to_step(market_reference_price, rounding_step)
    market_min = round_to_step(p25, rounding_step)
    market_max = round_to_step(p75, rounding_step)
    purchase_price = round_to_step(purchase_price_raw, rounding_step)
    purchase_min = round_to_step(max(0, purchase_price - price_range_padding), rounding_step) if purchase_price else None
    purchase_max = round_to_step(purchase_price + price_range_padding, rounding_step) if purchase_price else None
    recommended_offer = round_to_step(recommended_offer_raw, rounding_step)
    target_purchase = round_to_step(target_purchase_raw, rounding_step)
    max_purchase = round_to_step(max_purchase_raw, rounding_step)

    pricing_adjustments = [
        {"type": "market_baseline", "label": "Giá trung vị thị trường", "amount": market_reference_price},
        {"type": "condition_discount", "label": "Điều chỉnh do condition tổng thể", "amount": -condition_discount},
    ]
    if trust_penalty:
        pricing_adjustments.append({"type": "trust_penalty", "label": "Trust penalty do thiếu ảnh hoặc xung đột thông tin", "amount": -trust_penalty})
    pricing_adjustments.extend(damage_adjustments)
    pricing_adjustments.extend(
        [
            {"type": "reconditioning_cost", "label": "Chi phí dọn sửa dự kiến", "amount": -recon_cost},
            {"type": "risk_buffer", "label": "Risk buffer", "amount": -risk_buffer},
            {"type": "target_margin", "label": "Biên lợi nhuận mục tiêu", "amount": -target_margin},
        ]
    )

    purchase_label = "Giá thu vào đề xuất"
    if result_type == "low_data_model_estimate":
        purchase_label = "Giá thu vào tham khảo, độ tin cậy thấp do dữ liệu thị trường còn ít"
    elif result_type != "standard_estimate":
        purchase_label = "Giá thu vào tham khảo do chưa đủ dữ liệu đúng phiên bản"

    rough_purchase_range = None
    if result_type == "rough_segment_estimate":
        rough_purchase_range = {
            "min": round_to_step(max(0, fair_price - price_range_padding), rounding_step),
            "max": round_to_step(fair_price + price_range_padding, rounding_step),
        }

    return {
        "marketReferencePrice": {
            "median": market_reference_price,
            "range": {"min": market_min, "max": market_max},
            "label": "Giá rao bán thị trường tham khảo",
        },
        "fairPrice": {
            "rawSuggestedPrice": fair_price_raw,
            "suggestedPrice": fair_price,
            "range": {"min": fair_min, "max": fair_max},
            "label": "Giá hợp lý sau khi xét condition và trust",
            "roundingStep": rounding_step,
            "roundingNote": rounding_note,
        },
        "dealSuggestion": {
            "rawRecommendedOfferPrice": recommended_offer_raw,
            "rawTargetPurchasePrice": target_purchase_raw,
            "rawMaxAcceptablePurchasePrice": max_purchase_raw,
            "recommendedOfferPrice": recommended_offer,
            "targetPurchasePrice": target_purchase,
            "maxAcceptablePurchasePrice": max_purchase,
            "negotiationRange": {"start": recommended_offer, "target": target_purchase, "ceiling": max_purchase},
            "label": "Gợi ý mức mua/deal",
            "talkingPoints": build_talking_points(damage_list, trust_assessment),
        },
        "marketSellingPrice": {
            "suggestedPrice": market_reference_price,
            "minPrice": market_min,
            "maxPrice": market_max,
            "label": "Giá bán ra thị trường tham khảo",
        },
        "purchasePrice": {
            "rawSuggestedPrice": purchase_price_raw,
            "suggestedPrice": purchase_price,
            "minPrice": purchase_min,
            "maxPrice": purchase_max,
            "label": purchase_label,
            "roundingStep": rounding_step,
            "roundingNote": rounding_note,
        },
        "roughPurchaseRange": rough_purchase_range,
        "pricingBreakdown": {
            "marketMedianPrice": market_reference_price,
            "conditionAdjustment": -condition_discount,
            "visualAdjustment": 0,
            "trustAdjustment": -trust_penalty,
            "baseReconditioningCost": base_reconditioning_cost,
            "damageRepairCost": damage_repair_cost,
            "estimatedReconditioningCost": recon_cost,
            "riskBuffer": risk_buffer,
            "targetMargin": target_margin,
            "roundingStep": rounding_step,
            "rawRecommendedOfferPrice": recommended_offer_raw,
            "rawTargetPurchasePrice": target_purchase_raw,
            "rawMaxAcceptablePurchasePrice": max_purchase_raw,
            "rawFairPrice": fair_price_raw,
        },
        "pricingAdjustments": pricing_adjustments,
    }


def condition_discount_rate(condition: dict[str, Any]) -> float:
    quality = int(condition.get("carQualityScore") or 0)
    if quality >= 80:
        return 0.0
    if quality >= 70:
        return 0.01
    if quality >= 60:
        return 0.025
    if quality >= 50:
        return 0.04
    return 0.06


def risk_buffer_rate(condition: dict[str, Any], fallback_level: int, variant_confidence: float, risk_assessment: dict[str, Any]) -> float:
    base = 0.015
    if fallback_level >= 3:
        base += 0.015
    if variant_confidence < 0.7:
        base += 0.01
    risk_score = int(risk_assessment.get("riskScore") or 0)
    if risk_score >= 46:
        base += 0.015
    elif risk_score >= 21:
        base += 0.008
    missing_count = len(condition.get("warnings") or [])
    if missing_count >= 2:
        base += 0.01
    return min(base, 0.07)


def target_margin_rate(vehicle_input: dict[str, Any]) -> float:
    title = str(vehicle_input.get("title") or "").lower()
    return 0.12 if any(brand in title for brand in LUXURY_BRANDS) else 0.08


def build_reconditioning_adjustments(market_reference_price: int, damage_list: list[dict[str, Any]], condition: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    total = 0
    adjustments = []
    severity_caps = {"minor": 7_000_000, "medium": 18_000_000, "major": 35_000_000, "critical": 60_000_000}
    grouped_minor = 0
    for item in damage_list:
        severity = str(item.get("severity") or "minor")
        amount = {
            "minor": max(1_500_000, int(round(market_reference_price * 0.003))),
            "medium": max(5_000_000, int(round(market_reference_price * 0.01))),
            "major": max(12_000_000, int(round(market_reference_price * 0.024))),
            "critical": max(25_000_000, int(round(market_reference_price * 0.045))),
        }.get(severity, max(1_500_000, int(round(market_reference_price * 0.003))))
        if severity == "minor":
            grouped_minor += amount
            amount = 0
        else:
            total += min(amount, severity_caps[severity])
            item["pricingImpact"] = -min(amount, severity_caps[severity])
            adjustments.append({"type": item.get("issue") or "damage", "label": item.get("label") or "Dieu chinh do hu hai", "amount": -min(amount, severity_caps[severity]), "evidenceImages": item.get("evidenceImages", [])})

    if grouped_minor:
        grouped_minor = min(grouped_minor, severity_caps["minor"])
        total += grouped_minor
        adjustments.append({"type": "minor_cosmetic_reconditioning", "label": "Chi phi xu ly hao mon ngoai that/noi that nhe", "amount": -grouped_minor, "evidenceImages": []})

    quality = int(condition.get("carQualityScore") or 0)
    if quality < 70 and total == 0:
        extra = max(3_000_000, int(round(market_reference_price * 0.006)))
        total += extra
        adjustments.append({"type": "general_reconditioning", "label": "Chi phi lam dep tong the", "amount": -extra, "evidenceImages": []})
    return total, adjustments


def compute_base_reconditioning_cost(market_reference_price: int) -> int:
    if market_reference_price < 500_000_000:
        return 3_000_000
    if market_reference_price < 1_000_000_000:
        return 6_000_000
    return max(8_000_000, int(round(market_reference_price * 0.01)))


def compute_trust_penalty(market_reference_price: int, trust_assessment: dict[str, Any]) -> int:
    trust_score = float(trust_assessment.get("trustScore") or 0)
    if trust_score >= 0.8:
        return 0
    if trust_score >= 0.6:
        return max(2_000_000, int(round(market_reference_price * 0.006)))
    if trust_score >= 0.4:
        return max(4_000_000, int(round(market_reference_price * 0.01)))
    return max(7_000_000, int(round(market_reference_price * 0.016)))


def build_talking_points(damage_list: list[dict[str, Any]], trust_assessment: dict[str, Any]) -> list[str]:
    points = []
    for item in damage_list:
        label = str(item.get("label") or "").strip()
        if label:
            points.append(f"{label} can duoc tru gia khi thuong luong.")
    for flag in trust_assessment.get("trustFlags", [])[:3]:
        message = str(flag.get("message") or "").strip()
        if message:
            points.append(message)
    if not points:
        points.append("Xe can kiem tra thuc te them truoc khi chot gia cuoi.")
    return list(dict.fromkeys(points))


def price_rounding_step(market_reference_price: int | None) -> int:
    if not market_reference_price:
        return 5_000_000
    if market_reference_price < 1_000_000_000:
        return 5_000_000
    return 10_000_000


def round_to_step(value: int | None, step: int) -> int | None:
    if value is None:
        return None
    if step <= 0:
        return value
    return int(round(value / step) * step)
