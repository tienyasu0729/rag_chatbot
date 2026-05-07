"""
Similarity scoring, weighting va market stats.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

from app.pricing.text_analysis_service import normalize_fuel, normalize_origin, normalize_text, normalize_transmission

MIN_ELIGIBLE_SCORE = 55
STRONG_COMPARABLE_SCORE = 70


def score_and_filter_candidates(
    vehicle_input: dict[str, Any],
    text_analysis: dict[str, Any],
    listings: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates = []
    scored_count = 0
    model_keyword = normalize_text(str(text_analysis.get("modelKeyword") or ""))
    input_variant = normalize_text(str(text_analysis.get("detectedVariant") or ""))
    target_year = _to_int(vehicle_input.get("year"))
    target_mileage = _to_int(vehicle_input.get("mileage"))
    target_transmission = text_analysis.get("normalizedTransmission")
    target_fuel = text_analysis.get("normalizedFuel")
    target_origin = text_analysis.get("normalizedOrigin")
    body_style = normalize_text(str(vehicle_input.get("bodyStyle") or ""))

    for item in listings:
        candidate = dict(item)
        candidate["warnings"] = []
        candidate["dataQualityFlags"] = []
        candidate["weightAdjustmentReasons"] = []
        candidate["excludedReason"] = None
        candidate["usedForPricing"] = False
        candidate["weight"] = 0.0

        price = _to_int(item.get("price"))
        year = _to_int(item.get("year"))
        title = normalize_text(str(item.get("title") or ""))
        if not price or not year or not title:
            candidate["excludedReason"] = "missing_required_fields"
            candidates.append(candidate)
            continue

        scored_count += 1
        year_delta = abs(year - target_year) if target_year is not None else None
        transmission = normalize_transmission(item.get("transmission"))
        fuel = normalize_fuel(item.get("fuel"))
        origin = normalize_origin(item.get("origin"))
        title_tokens = set(title.split())
        transmission_match = bool(transmission and target_transmission and transmission == target_transmission)
        transmission_mismatch = bool(transmission and target_transmission and transmission != target_transmission)

        variant_match = classify_variant_match(input_variant, title, title_tokens)
        score = 0
        if item.get("categoryId") == vehicle_input.get("categoryId"):
            score += 15
        if item.get("subcategoryId") == vehicle_input.get("subcategoryId"):
            score += 15
        if model_keyword and model_keyword in title:
            score += 35
        if year_delta is not None:
            if year_delta == 0:
                score += 15
            elif year_delta == 1:
                score += 10
            elif year_delta == 2:
                score += 5
            elif year_delta == 3:
                score += 1
            elif year_delta == 4:
                score -= 5
        if target_mileage is not None:
            mileage = _to_int(item.get("mileage"))
            if mileage in {None, 0}:
                candidate["dataQualityFlags"].append("mileage_unknown_or_zero")
                candidate["weightAdjustmentReasons"].append("Da giam trong so do mileage khong dang tin.")
            elif mileage is not None:
                gap = abs(mileage - target_mileage)
                if gap <= 10000:
                    score += 10
                elif gap <= 30000:
                    score += 6
                elif gap <= 50000:
                    score += 3
        if transmission_match:
            score += 10
        elif transmission_mismatch:
            score -= 10
        if fuel and fuel == target_fuel:
            score += 5
        if origin and origin == target_origin:
            score += 3
        if body_style and normalize_text(str(item.get("bodyStyle") or "")) == body_style:
            score += 4
        if item.get("branchId") and item.get("branchId") == vehicle_input.get("branchId"):
            score += 2
        score += variant_bonus(variant_match)
        score -= recency_penalty(item.get("postingDate"))

        candidate["similarityScore"] = max(score, 0)
        candidate["variantMatch"] = variant_match
        candidate["variantDetected"] = extract_candidate_variant(title_tokens)
        candidate["yearDelta"] = year_delta
        candidate["transmissionMismatch"] = transmission_mismatch

        if year_delta is not None and year_delta > 4:
            candidate["excludedReason"] = "year_delta_too_high"
            candidate["warnings"].append("Lech doi qua xa so voi xe input.")
            candidates.append(candidate)
            continue

        if candidate["similarityScore"] < MIN_ELIGIBLE_SCORE:
            candidate["excludedReason"] = (
                "low_similarity_different_transmission"
                if transmission and target_transmission and transmission != target_transmission
                else "low_similarity"
            )
            candidates.append(candidate)
            continue

        weight = compute_candidate_weight(
            variant_match=variant_match,
            similarity_score=candidate["similarityScore"],
            year_delta=year_delta,
            transmission_match=transmission_match,
            posting_date=item.get("postingDate"),
            mileage=item.get("mileage"),
            weight_adjustment_reasons=candidate["weightAdjustmentReasons"],
        )
        if weight <= 0:
            candidate["excludedReason"] = "low_weight_after_variant_penalty"
            candidates.append(candidate)
            continue

        candidate["weight"] = round(weight, 4)
        if variant_match == "different_variant":
            candidate["warnings"].append("Khac phien ban/hop so so voi xe input.")
        if transmission_mismatch:
            candidate["warnings"].append("Khac hop so so voi xe input.")
        candidates.append(candidate)

    sorted_candidates = sorted(candidates, key=lambda row: (row.get("similarityScore", 0), row.get("weight", 0)), reverse=True)
    eligible_candidates = [row for row in sorted_candidates if not row.get("excludedReason")]
    strong_candidates = [row for row in eligible_candidates if row["similarityScore"] >= STRONG_COMPARABLE_SCORE]
    weak_candidates = [row for row in eligible_candidates if MIN_ELIGIBLE_SCORE <= row["similarityScore"] < STRONG_COMPARABLE_SCORE]

    used_candidates = strong_candidates[:]
    if len(used_candidates) < 5:
        for row in weak_candidates:
            if row not in used_candidates:
                used_candidates.append(row)
            if len(used_candidates) >= 5:
                break
    for row in used_candidates:
        row["usedForPricing"] = True

    return {
        "candidates": sorted_candidates,
        "scoredCount": scored_count,
        "eligibleCount": len(eligible_candidates),
        "usedForPricingCount": len(used_candidates),
    }


def build_market_stats(scored: dict[str, Any], market_window_days: int, similar_found: int) -> dict[str, Any]:
    candidates = scored["candidates"]
    eligible = [item for item in candidates if not item.get("excludedReason")]
    prelim_used = [item for item in candidates if item.get("usedForPricing")]
    inliers = remove_outliers(prelim_used)
    removed_ids = {item["listingId"] for item in prelim_used if item not in inliers and item.get("listingId")}

    final_candidates = []
    for item in candidates:
        clone = dict(item)
        if clone.get("listingId") in removed_ids:
            clone["usedForPricing"] = False
            clone["excludedReason"] = "price_outlier"
        elif clone.get("listingId") not in {used.get("listingId") for used in inliers}:
            clone["usedForPricing"] = False
        final_candidates.append(clone)

    used = [item for item in final_candidates if item.get("usedForPricing") and float(item.get("weight") or 0) > 0]
    prices = [int(item["price"]) for item in used if _to_int(item.get("price"))]
    raw_prices = [int(item["price"]) for item in eligible if _to_int(item.get("price"))]
    if not prices:
        return {
            "similarListingsFound": similar_found,
            "similarListingsUsed": 0,
            "sampleSize": 0,
            "effectiveSampleSize": 0,
            "totalWeight": 0,
            "statisticalStrength": "low",
            "observedMinPrice": None,
            "observedMaxPrice": None,
            "outliersRemoved": max(0, len(prelim_used) - len(inliers)),
            "priceStatisticMethod": "weighted_median",
            "rawMedianPrice": None,
            "medianPrice": None,
            "p25Price": None,
            "p75Price": None,
            "weightedMedianPrice": None,
            "weightedP25Price": None,
            "weightedP75Price": None,
            "weightedMedianNote": None,
            "averageSimilarityScore": 0,
            "note": "Khong du candidate dat nguong de tinh gia.",
            "marketWindowDays": market_window_days,
            "filteredListings": [],
            "scoredCount": scored["scoredCount"],
            "eligibleCount": scored["eligibleCount"],
            "usedForPricingCount": 0,
            "allCandidates": final_candidates,
        }

    weights = [float(item["weight"]) for item in used]
    total_weight = sum(weights)
    effective_sample_size = 0.0
    if total_weight > 0:
        effective_sample_size = (total_weight ** 2) / sum(weight ** 2 for weight in weights)
    weighted_pairs = [(int(item["price"]), float(item["weight"])) for item in used]
    weighted_pairs.sort(key=lambda pair: pair[0])
    raw_median = int(percentile(raw_prices or prices, 50))
    weighted_median = int(weighted_percentile(weighted_pairs, 0.5))
    weighted_p25 = int(weighted_percentile(weighted_pairs, 0.25))
    weighted_p75 = int(weighted_percentile(weighted_pairs, 0.75))
    avg_similarity = round(sum(float(item["similarityScore"]) for item in used) / len(used), 2)
    sample_size = len(used)

    if sample_size >= 25 and effective_sample_size >= 10:
        strength = "high"
    elif sample_size >= 10 and effective_sample_size >= 6:
        strength = "medium"
    else:
        strength = "low"

    return {
        "similarListingsFound": similar_found,
        "similarListingsUsed": sample_size,
        "sampleSize": sample_size,
        "effectiveSampleSize": round(effective_sample_size, 2),
        "totalWeight": round(total_weight, 2),
        "statisticalStrength": strength,
        "observedMinPrice": min(prices),
        "observedMaxPrice": max(prices),
        "outliersRemoved": max(0, len(prelim_used) - len(inliers)),
        "priceStatisticMethod": "weighted_median",
        "rawMedianPrice": raw_median,
        "medianPrice": weighted_median,
        "p25Price": weighted_p25,
        "p75Price": weighted_p75,
        "weightedMedianPrice": weighted_median,
        "weightedP25Price": weighted_p25,
        "weightedP75Price": weighted_p75,
        "weightedMedianNote": (
            "Weighted median trung voi median thuong trong mau hien tai."
            if raw_median == weighted_median
            else "Weighted median uu tien comparable gan xe input hon so voi median thuong."
        ),
        "averageSimilarityScore": avg_similarity,
        "note": "Mau du lieu it, khoang gia chi mang tinh quan sat." if sample_size < 10 else None,
        "marketWindowDays": market_window_days,
        "filteredListings": used,
        "scoredCount": scored["scoredCount"],
        "eligibleCount": scored["eligibleCount"],
        "usedForPricingCount": sample_size,
        "allCandidates": final_candidates,
    }


def classify_variant_match(input_variant: str, title: str, title_tokens: set[str]) -> str:
    if not input_variant:
        return "unknown"
    if input_variant in title:
        return "exact"
    input_tokens = [token for token in input_variant.split() if token]
    if not input_tokens:
        return "unknown"
    matched = [token for token in input_tokens if token in title_tokens]
    if matched and len(matched) >= max(1, len(input_tokens) // 2):
        return "partial"
    variant_tokens = {"g", "e", "v", "cvt", "at", "mt", "1.5", "1.8", "2.0"}
    if any(token in title_tokens for token in variant_tokens):
        return "different_variant"
    return "unknown"


def variant_bonus(variant_match: str) -> int:
    return {
        "exact": 15,
        "partial": 8,
        "unknown": 0,
        "different_variant": -8,
    }.get(variant_match, 0)


def compute_candidate_weight(
    *,
    variant_match: str,
    similarity_score: int,
    year_delta: int | None,
    transmission_match: bool,
    posting_date: Any,
    mileage: Any,
    weight_adjustment_reasons: list[str] | None = None,
) -> float:
    reasons = weight_adjustment_reasons if weight_adjustment_reasons is not None else []
    base = {
        "exact": 1.0,
        "partial": 0.72,
        "unknown": 0.6 if transmission_match else 0.48,
        "different_variant": 0.4 if transmission_match else 0.28,
    }.get(variant_match, 0.4)
    if year_delta is not None:
        if year_delta == 1:
            base *= 0.9
        elif year_delta == 2:
            base *= 0.72
        elif year_delta == 3:
            base *= 0.55
        elif year_delta == 4:
            base *= 0.3
    if not transmission_match and variant_match == "different_variant":
        base *= 0.8
        reasons.append("Da giam trong so do khac phien ban/hop so.")
    mileage_value = _to_int(mileage)
    if mileage_value in {None, 0}:
        base *= 0.85
        reasons.append("Khong cong diem mileage similarity va giam trong so 15%.")
    recency_days = days_since(posting_date)
    if recency_days is not None:
        if recency_days > 365:
            base *= 0.8
            reasons.append("Da giam trong so do du lieu dang tin cu hon 365 ngay.")
        elif recency_days > 180:
            base *= 0.9
            reasons.append("Da giam trong so do du lieu cu hon 180 ngay.")
        elif recency_days > 90:
            base *= 0.95
            reasons.append("Da giam nhe trong so do du lieu qua 90 ngay.")
    if similarity_score < 70:
        base *= 0.75
        reasons.append("Comparable chi dat similarity trung binh-thap.")
    elif similarity_score > 85:
        base *= 1.05
    return round(max(base, 0.0), 4)


def remove_outliers(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prices = [int(item["price"]) for item in candidates if _to_int(item.get("price"))]
    if len(prices) < 4:
        return candidates
    q1 = percentile(prices, 25)
    q3 = percentile(prices, 75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return [item for item in candidates if low <= float(item["price"]) <= high]


def weighted_percentile(weighted_pairs: list[tuple[int, float]], percentile_value: float) -> float:
    total_weight = sum(weight for _, weight in weighted_pairs)
    if total_weight <= 0:
        return 0.0
    target = total_weight * percentile_value
    cumulative = 0.0
    for price, weight in weighted_pairs:
        cumulative += weight
        if cumulative >= target:
            return float(price)
    return float(weighted_pairs[-1][0])


def percentile(values: list[int], pct: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (pct / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[low])
    weight = rank - low
    return float(ordered[low] * (1 - weight) + ordered[high] * weight)


def days_since(value: Any) -> int | None:
    if not value:
        return None
    try:
        posting_date = datetime.strptime(str(value), "%Y-%m-%d").date()
        return (date.today() - posting_date).days
    except ValueError:
        return None


def recency_penalty(value: Any) -> int:
    age = days_since(value)
    if age is None:
        return 0
    if age > 365:
        return 15
    if age > 180:
        return 10
    if age > 90:
        return 5
    return 0


def extract_candidate_variant(title_tokens: set[str]) -> str | None:
    ordered = [token.upper() for token in ["g", "e", "v", "1.5", "1.8", "2.0", "cvt", "at", "mt"] if token in title_tokens]
    return " ".join(ordered) or None


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
