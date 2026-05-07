"""
Phan tich title/descriptions cho variant matching.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


TRANSMISSION_MAP = {
    "at": "automatic",
    "auto": "automatic",
    "automatic": "automatic",
    "tu dong": "automatic",
    "so tu dong": "automatic",
    "tu ong": "automatic",
    "so tu ong": "automatic",
    "t ng": "automatic",
    "ta aatmng": "automatic",
    "sa ta aatmng": "automatic",
    "cvt": "automatic",
    "mt": "manual",
    "manual": "manual",
    "so san": "manual",
    "dct": "automatic",
}

FUEL_MAP = {
    "xang": "gasoline",
    "may xang": "gasoline",
    "gasoline": "gasoline",
    "petrol": "gasoline",
    "diesel": "diesel",
    "dau": "diesel",
    "may dau": "diesel",
    "hybrid": "hybrid",
    "dien": "electric",
    "electric": "electric",
}

ORIGIN_MAP = {
    "trong nuoc": "domestic",
    "lap rap trong nuoc": "domestic",
    "lap rap": "domestic",
    "nhap khau": "imported",
    "imported": "imported",
}

VARIANT_TOKENS = {
    "g",
    "e",
    "v",
    "rs",
    "luxury",
    "premium",
    "deluxe",
    "standard",
    "xls",
    "xlt",
    "wildtrak",
    "raptor",
    "titanium",
    "ambiente",
    "trend",
    "2.0",
    "2.5",
    "1.5",
    "1.8",
    "4x2",
    "4x4",
    "awd",
    "hybrid",
    "turbo",
    "diesel",
    "cvt",
    "at",
    "mt",
}

NEGATIVE_SIGNALS = {
    "dam dung": "Co tin hieu mo ta va cham.",
    "ngap nuoc": "Co tin hieu mo ta ngap nuoc.",
    "chay dich vu": "Co tin hieu xe tung chay dich vu.",
}

POSITIVE_SIGNALS = {
    "bao duong hang": "bao duong hang",
    "bao duong chinh hang": "bao duong hang",
    "chinh chu": "chinh chu",
}

KNOWN_BRANDS = {
    "toyota",
    "honda",
    "ford",
    "kia",
    "hyundai",
    "mazda",
    "mitsubishi",
    "vinfast",
    "chevrolet",
    "nissan",
    "suzuki",
    "mercedes",
    "bmw",
    "audi",
    "lexus",
    "peugeot",
    "isuzu",
    "volkswagen",
    "subaru",
}


def analyze_vehicle_text(vehicle_input: dict[str, Any], candidate_titles: list[str] | None = None) -> dict[str, Any]:
    title = str(vehicle_input.get("title") or "").strip()
    description = str(vehicle_input.get("description") or "").strip()
    normalized_title = normalize_text(title)
    normalized_description = normalize_text(description)
    title_tokens = tokenise(normalized_title)
    variant_tokens = [token for token in title_tokens if token in VARIANT_TOKENS]
    year = vehicle_input.get("year")
    transmission = normalize_transmission(vehicle_input.get("transmission"))
    fuel = normalize_fuel(vehicle_input.get("fuel"))
    origin = normalize_origin(vehicle_input.get("origin"))
    brand_keyword, model_keyword = extract_brand_model_keywords(title_tokens)

    matched_titles = []
    best_ratio = 0.0
    for item in candidate_titles or []:
        ratio = SequenceMatcher(a=normalized_title, b=normalize_text(item)).ratio()
        matched_titles.append({"title": item, "score": round(ratio, 4)})
        best_ratio = max(best_ratio, ratio)

    variant_confidence = 0.55
    if variant_tokens:
        variant_confidence += 0.15
    if transmission:
        variant_confidence += 0.1
    if fuel:
        variant_confidence += 0.05
    if year:
        variant_confidence += 0.05
    if model_keyword:
        variant_confidence += 0.03
    if best_ratio >= 0.9:
        variant_confidence += 0.1
    elif best_ratio >= 0.8:
        variant_confidence += 0.05
    variant_confidence = min(0.95, round(variant_confidence, 2))

    positive = [label for key, label in POSITIVE_SIGNALS.items() if key in normalized_description]
    negative = [label for key, label in NEGATIVE_SIGNALS.items() if key in normalized_description]

    detected_variant = " ".join(dict.fromkeys(variant_tokens)).upper() if variant_tokens else infer_variant_from_title(title_tokens)
    input_conflicts = []
    if transmission == "manual" and any(token in {"at", "cvt", "automatic"} for token in title_tokens):
        input_conflicts.append("Transmission input mau thuan voi title chua AT/CVT.")
    if transmission == "automatic" and any(token in {"mt", "manual"} for token in title_tokens):
        input_conflicts.append("Transmission input mau thuan voi title chua MT/manual.")

    return {
        "normalizedTitle": normalized_title,
        "normalizedDescription": normalized_description,
        "titleTokens": title_tokens,
        "detectedBrand": brand_keyword.title() if brand_keyword else None,
        "detectedModel": model_keyword.title() if model_keyword else None,
        "brandKeyword": brand_keyword,
        "modelKeyword": model_keyword,
        "detectedVariant": detected_variant or None,
        "variantConfidence": variant_confidence,
        "normalizedFuel": fuel or normalize_text(str(vehicle_input.get("fuel") or "")),
        "normalizedTransmission": transmission or normalize_text(str(vehicle_input.get("transmission") or "")),
        "normalizedOrigin": origin or normalize_text(str(vehicle_input.get("origin") or "")),
        "positiveSignals": positive,
        "negativeSignals": negative,
        "riskFlags": negative.copy(),
        "inputConflicts": input_conflicts,
        "matchedCandidateTitles": sorted(matched_titles, key=lambda item: item["score"], reverse=True)[:10],
        "aiConfirmationUsed": False,
    }


def normalize_text(value: str) -> str:
    value = repair_common_mojibake(value or "")
    value = value.replace("\u0110", "D").replace("\u0111", "d")
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().replace("/", " ").replace("-", " ")
    ascii_text = re.sub(r"[^a-z0-9.\s]", " ", ascii_text)
    return " ".join(ascii_text.split())


def tokenise(value: str) -> list[str]:
    return [token for token in value.split() if token]


def normalize_transmission(value: Any) -> str:
    normalized = normalize_text(str(value or ""))
    return TRANSMISSION_MAP.get(normalized, TRANSMISSION_MAP.get(normalized.replace(".", ""), normalized))


def normalize_fuel(value: Any) -> str:
    normalized = normalize_text(str(value or ""))
    return FUEL_MAP.get(normalized, normalized)


def normalize_origin(value: Any) -> str:
    normalized = normalize_text(str(value or ""))
    return ORIGIN_MAP.get(normalized, normalized)


def extract_brand_model_keywords(tokens: list[str]) -> tuple[str | None, str | None]:
    if not tokens:
        return None, None
    brand = tokens[0] if tokens[0] in KNOWN_BRANDS else None
    search_tokens = tokens[1:] if brand else tokens
    model = next(
        (
            token
            for token in search_tokens
            if token not in VARIANT_TOKENS
            and not re.fullmatch(r"\d{4}", token)
            and not re.fullmatch(r"\d\.\d", token)
            and token not in {"automatic", "manual", "diesel", "gasoline", "hybrid", "electric"}
        ),
        None,
    )
    return brand, model


def infer_variant_from_title(tokens: list[str]) -> str:
    collected = []
    for token in tokens:
        if token in VARIANT_TOKENS or re.fullmatch(r"\d\.\d", token):
            collected.append(token.upper())
    return " ".join(dict.fromkeys(collected))


def repair_common_mojibake(value: str) -> str:
    suspicious_markers = ("Ã", "Ä", "á", "Â")
    if not any(marker in value for marker in suspicious_markers):
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
