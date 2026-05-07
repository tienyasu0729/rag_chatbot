"""
Tong hop inspection thanh quality/risk/trust/damage.
"""

from __future__ import annotations

from statistics import mean
from typing import Any


def aggregate_condition(*, processed_images: dict[str, Any], text_analysis: dict[str, Any], inspection: dict[str, Any]) -> dict[str, Any]:
    inspection_groups = inspection.get("inspectionGroups", {})
    scores = {name: int(group.get("score") or 0) for name, group in inspection_groups.items()}
    quality_score = int(round(mean(scores.values()))) if scores else 72
    exterior_score = _mean_group(scores, ["front", "rear", "left_side", "right_side", "damage_detail"])
    interior_score = _mean_group(scores, ["interior_front", "interior_rear", "dashboard", "odometer"])
    engine_bay_score = scores.get("engine_bay")

    damage_list = deduplicate_damage_list(inspection.get("damageFindings", []))
    visible_damage = bool(damage_list)

    warnings = [f"Thieu anh {item}." for item in processed_images.get("missingViews", [])]
    if processed_images.get("partialViews"):
        warnings.extend([f"Anh {item} chi o muc bao phu mot phan." for item in processed_images["partialViews"]])

    trust_flags = []
    for asset in processed_images.get("acceptedAssets", []):
        if asset.group_mismatch and asset.group_warning:
            trust_flags.append({"type": "group_mismatch_resolved", "severity": "low", "message": asset.group_warning})
        if not asset.include_in_condition_scoring and asset.declared_group == "document":
            trust_flags.append({"type": "document_image_not_used_for_condition", "severity": "info", "message": "Anh giay to khong duoc dung de danh gia tinh trang xe."})

    for view in processed_images.get("missingViews", []):
        trust_flags.append(
            {
                "type": f"missing_{view}",
                "severity": "medium" if view in {"odometer", "engine_bay"} else "low",
                "message": f"Chua co anh {view} de doi chieu day du.",
            }
        )
    for conflict in text_analysis.get("inputConflicts", []):
        trust_flags.append({"type": "metadata_conflict", "severity": "medium", "message": conflict})

    risk_flags = list(inspection.get("riskFlags", []))
    consistency_flags = build_consistency_flags(text_analysis, damage_list)
    trust_flags.extend(consistency_flags)

    risk_score = compute_risk_score(damage_list, risk_flags, processed_images)
    trust_score = compute_trust_score(trust_flags, processed_images)
    coverage_confidence = build_coverage_confidence(processed_images)

    return {
        "conditionAssessment": {
            "overallScore": round(quality_score / 10, 1),
            "label": label_for_quality(quality_score),
            "confidence": round(min(0.95, max(0.35, coverage_confidence * trust_score)), 2),
            "visibleDamage": visible_damage,
            "carQualityScore": quality_score,
            "exteriorScore": exterior_score,
            "interiorScore": interior_score,
            "engineBayScore": engine_bay_score,
            "damageFindings": damage_list,
            "warnings": warnings,
        },
        "riskAssessment": {
            "riskScore": risk_score,
            "riskLevel": risk_level(risk_score),
            "direction": "higher_is_riskier",
            "riskFlags": risk_flags,
        },
        "trustAssessment": {
            "trustScore": round(trust_score, 2),
            "trustLabel": trust_label(trust_score),
            "direction": "higher_is_more_trustworthy",
            "trustFlags": trust_flags,
        },
        "damageList": damage_list,
    }


def deduplicate_damage_list(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for finding in findings:
        key = (
            str(finding.get("issue") or "").strip().lower(),
            normalize_location(str(finding.get("location") or "")),
            str(finding.get("severity") or "minor").strip().lower(),
        )
        item = grouped.get(key)
        if item is None:
            grouped[key] = dict(finding)
            grouped[key]["countedOnce"] = True
            continue
        evidence = set(item.get("evidenceImages", []))
        evidence.update(finding.get("evidenceImages", []))
        item["evidenceImages"] = sorted(evidence)
        item["confidence"] = max(float(item.get("confidence") or 0), float(finding.get("confidence") or 0))
    return list(grouped.values())


def build_consistency_flags(text_analysis: dict[str, Any], damage_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flags = []
    normalized = str(text_analysis.get("normalizedDescription") or "")
    has_cosmetic_damage = any(item.get("issue") in {"scratch", "dent", "wear", "seat_wear"} for item in damage_list)
    has_repaint = any(item.get("issue") == "possible_repaint" for item in damage_list)
    has_seat_wear = any(item.get("issue") == "seat_wear" and severity_rank(item.get("severity")) >= 2 for item in damage_list)

    if any(token in normalized for token in ["khong tray xuoc", "khong mop", "khong xuoc"]) and has_cosmetic_damage:
        flags.append({"type": "description_conflict", "severity": "medium", "message": "Mo ta noi khong tray xuoc nhung anh co dau hieu hao mon hoac tray xuoc."})
    elif "khong loi" in normalized:
        flags.append({"type": "description_consistency_note", "severity": "low", "message": "Mo ta cam ket khong loi; anh chua du de xac minh may hop so nen can kiem tra thuc te."})

    if any(token in normalized for token in ["zin 100", "zin", "son zin"]) and has_repaint:
        flags.append({"type": "description_conflict", "severity": "medium", "message": "Mo ta noi xe zin nhung anh co dau hieu nghi son lai, can kiem tra thuc te."})
    if any(token in normalized for token in ["odo thap", "it di", "di gia dinh"]) and has_seat_wear:
        flags.append({"type": "odo_consistency_risk", "severity": "medium", "message": "Mo ta cho thay xe it di nhung noi that co dau hieu hao mon ro hon mong doi."})
    return flags


def compute_risk_score(damage_list: list[dict[str, Any]], risk_flags: list[dict[str, Any]], processed_images: dict[str, Any]) -> int:
    score = 8
    for view in processed_images.get("missingViews", []):
        if view in {"engine_bay", "odometer"}:
            score += 10
        else:
            score += 4
    for damage in damage_list:
        score += {"minor": 3, "medium": 9, "major": 16, "critical": 28}.get(str(damage.get("severity")), 3)
    for flag in risk_flags:
        severity = str(flag.get("severity") or "low")
        score += {"low": 2, "medium": 6, "major": 12, "critical": 25}.get(severity, 2)
    return min(max(score, 0), 100)


def compute_trust_score(trust_flags: list[dict[str, Any]], processed_images: dict[str, Any]) -> float:
    score = 0.92
    score -= len(processed_images.get("missingViews", [])) * 0.05
    score -= len(processed_images.get("partialViews", [])) * 0.02
    for flag in trust_flags:
        severity = str(flag.get("severity") or "low")
        score -= {"info": 0.0, "low": 0.03, "medium": 0.07, "major": 0.12, "critical": 0.18}.get(severity, 0.03)
    return max(0.2, min(score, 0.95))


def build_coverage_confidence(processed_images: dict[str, Any]) -> float:
    full_count = len(processed_images.get("coveredViews", []))
    partial_count = len(processed_images.get("partialViews", []))
    missing_count = len(processed_images.get("missingViews", []))
    score = 0.45 + min(0.35, full_count * 0.04) + min(0.1, partial_count * 0.02) - min(0.25, missing_count * 0.03)
    return max(0.3, min(score, 0.95))


def label_for_quality(score: int) -> str:
    if score >= 85:
        return "Tot"
    if score >= 70:
        return "Kha"
    if score >= 55:
        return "Trung binh"
    if score >= 40:
        return "Kem"
    return "Rat kem"


def risk_level(score: int) -> str:
    if score >= 71:
        return "very_high"
    if score >= 46:
        return "high"
    if score >= 21:
        return "medium"
    return "low"


def trust_label(score: float) -> str:
    if score >= 0.8:
        return "Cao"
    if score >= 0.6:
        return "Trung binh"
    if score >= 0.4:
        return "Thap"
    return "Rat thap"


def severity_rank(value: Any) -> int:
    return {"minor": 1, "medium": 2, "major": 3, "critical": 4}.get(str(value or "").lower(), 1)


def normalize_location(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _mean_group(scores: dict[str, int], names: list[str]) -> int | None:
    values = [scores[name] for name in names if name in scores]
    if not values:
        return None
    return int(round(mean(values)))
