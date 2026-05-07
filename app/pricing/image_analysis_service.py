"""
Image processing cho internal pricing.
"""

from __future__ import annotations

import hashlib
import io
from collections import Counter
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from PIL import Image

from app.config import get_settings
from app.pricing.errors import PricingError

GROUPS = {
    "front",
    "rear",
    "left_side",
    "right_side",
    "interior_front",
    "interior_rear",
    "dashboard",
    "odometer",
    "engine_bay",
    "tire",
    "damage_detail",
    "document",
    "other",
}

ESSENTIAL_VIEWS = [
    "front",
    "rear",
    "left_side",
    "right_side",
    "interior_front",
    "dashboard",
    "engine_bay",
    "odometer",
]


@dataclass
class ProcessedImageAsset:
    url: str
    public_id: str
    source: str
    declared_group: str
    caption: str | None
    caption_by: str | None
    caption_type: str | None
    filename_hint_group: str
    caption_hint_group: str
    caption_claims: list[dict[str, Any]]
    detected_group: str
    detected_group_confidence: float
    resolved_groups: list[str]
    inspection_group: str | None
    include_in_condition_scoring: bool
    group_mismatch: bool
    group_warning: str | None
    exact_fingerprint: str
    perceptual_hash: str | None
    hash_source: str


def validate_and_process_assets(image_assets: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    allowed_domains = settings.pricing_cloudinary_domains
    max_images = settings.PRICING_MAX_IMAGES

    if not image_assets:
        raise PricingError("invalid_request", "imageAssets bat buoc phai co it nhat 1 phan tu", status_code=422)
    if len(image_assets) > max_images:
        raise PricingError("invalid_image_assets", f"So luong imageAssets vuot qua gioi han {max_images}", status_code=422)

    staged_assets = []
    exact_seen: set[str] = set()
    ignored_images: list[dict[str, Any]] = []
    exact_duplicates_removed = 0

    for asset in image_assets:
        source = str(asset.get("source") or "").strip().lower()
        declared_group = str(asset.get("declaredGroup") or "").strip()
        url = str(asset.get("url") or "").strip()
        public_id = str(asset.get("publicId") or "").strip()
        caption = str(asset.get("caption") or "").strip() or None
        caption_by = str(asset.get("captionBy") or "").strip() or None
        caption_type = str(asset.get("captionType") or "").strip() or None
        if source != "cloudinary":
            raise PricingError("invalid_image_assets", "Chi chap nhan imageAssets.source = cloudinary", status_code=422)
        if declared_group not in GROUPS:
            raise PricingError("invalid_image_assets", "declaredGroup khong hop le", status_code=422)
        if not url or not public_id:
            raise PricingError("invalid_image_assets", "imageAssets phai co url va publicId hop le", status_code=422)

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise PricingError("invalid_image_assets", "image URL khong hop le", status_code=422)
        if allowed_domains and parsed.netloc.lower() not in allowed_domains:
            raise PricingError("invalid_image_assets", "image URL khong thuoc Cloudinary allowed domain", status_code=422)

        exact_fingerprint = hashlib.sha256(f"{public_id}|{url}|{declared_group}".encode("utf-8")).hexdigest()
        if exact_fingerprint in exact_seen:
            exact_duplicates_removed += 1
            ignored_images.append({"url": url, "publicId": public_id, "reason": "exact_duplicate"})
            continue
        exact_seen.add(exact_fingerprint)

        filename_hint_group = infer_group_from_path(public_id, url)
        caption_analysis = parse_caption(caption)
        detected_group = filename_hint_group
        detected_group_confidence = confidence_for_hint(filename_hint_group)
        resolution = resolve_groups(
            declared_group,
            filename_hint_group,
            caption_analysis["captionHintGroup"],
            detected_group,
            detected_group_confidence,
        )
        staged_assets.append(
            {
                "url": url,
                "public_id": public_id,
                "source": source,
                "declared_group": declared_group,
                "caption": caption,
                "caption_by": caption_by,
                "caption_type": caption_type,
                "filename_hint_group": filename_hint_group,
                "caption_hint_group": caption_analysis["captionHintGroup"],
                "caption_claims": caption_analysis["captionClaims"],
                "detected_group": detected_group,
                "detected_group_confidence": detected_group_confidence,
                "resolved_groups": resolution["resolvedGroups"],
                "inspection_group": resolution["inspectionGroup"],
                "include_in_condition_scoring": resolution["includeInConditionScoring"],
                "group_mismatch": resolution["groupMismatch"],
                "group_warning": resolution["groupWarning"],
                "exact_fingerprint": exact_fingerprint,
            }
        )

    accepted: list[ProcessedImageAsset] = []
    kept_hashes: list[tuple[str, str]] = []
    near_duplicates_removed = 0
    multiple_assets = len(staged_assets) > 1

    for item in staged_assets:
        perceptual_hash = compute_perceptual_hash(item["url"]) if multiple_assets else None
        compare_group = item["inspection_group"] or item["declared_group"]
        if perceptual_hash:
            is_duplicate = False
            for kept_group, kept_hash in kept_hashes:
                if kept_group == compare_group and hamming_distance(perceptual_hash, kept_hash) <= 10:
                    is_duplicate = True
                    break
            if is_duplicate:
                near_duplicates_removed += 1
                ignored_images.append({"url": item["url"], "publicId": item["public_id"], "reason": "near_duplicate"})
                continue
            kept_hashes.append((compare_group, perceptual_hash))

        accepted.append(
            ProcessedImageAsset(
                url=item["url"],
                public_id=item["public_id"],
                source=item["source"],
                declared_group=item["declared_group"],
                caption=item["caption"],
                caption_by=item["caption_by"],
                caption_type=item["caption_type"],
                filename_hint_group=item["filename_hint_group"],
                caption_hint_group=item["caption_hint_group"],
                caption_claims=item["caption_claims"],
                detected_group=item["detected_group"],
                detected_group_confidence=item["detected_group_confidence"],
                resolved_groups=item["resolved_groups"],
                inspection_group=item["inspection_group"],
                include_in_condition_scoring=item["include_in_condition_scoring"],
                group_mismatch=item["group_mismatch"],
                group_warning=item["group_warning"],
                exact_fingerprint=item["exact_fingerprint"],
                perceptual_hash=perceptual_hash,
                hash_source="dhash" if perceptual_hash else "basic",
            )
        )

    groups = Counter(asset.declared_group for asset in accepted)
    covered_views, partial_views, inspection_groups = build_coverage(accepted)
    missing_views = [view for view in ESSENTIAL_VIEWS if view not in covered_views and view not in partial_views]
    incomplete_views = [
        {
            "view": view,
            "reason": "Chi thay mot phan goc chup, can bo sung anh ro hon de danh gia day du.",
        }
        for view in partial_views
    ]
    return {
        "acceptedAssets": accepted,
        "uploadedCount": len(image_assets),
        "validImageCount": len(staged_assets),
        "exactDuplicatesRemoved": exact_duplicates_removed,
        "nearDuplicatesRemoved": near_duplicates_removed,
        "analyzedCount": len(accepted),
        "groups": dict(groups),
        "coveredViews": covered_views,
        "partialViews": partial_views,
        "missingViews": missing_views,
        "incompleteViews": incomplete_views,
        "inspectionGroups": inspection_groups,
        "ignoredImages": ignored_images,
        "hashMode": "dhash" if any(asset.perceptual_hash for asset in accepted) else "basic",
    }


def resolve_groups(
    declared_group: str,
    filename_hint_group: str,
    caption_hint_group: str,
    detected_group: str,
    detected_group_confidence: float,
) -> dict[str, Any]:
    if declared_group == "document":
        return {
            "resolvedGroups": ["document"],
            "inspectionGroup": None,
            "includeInConditionScoring": False,
            "groupMismatch": filename_hint_group != "document",
            "groupWarning": "Anh giay to khong duoc dung de danh gia tinh trang xe.",
        }

    base_group = declared_group
    if filename_hint_group != "other" and declared_group in {"other", "front", "rear"}:
        base_group = filename_hint_group
    elif caption_hint_group != "other" and declared_group == "other":
        base_group = caption_hint_group
    if detected_group_confidence >= 0.75 and detected_group != "document":
        base_group = detected_group

    resolved_groups = [base_group]
    partial_dashboard = False
    if base_group == "interior_front":
        partial_dashboard = True
    if filename_hint_group == "dashboard" or caption_hint_group == "dashboard":
        partial_dashboard = True
    if partial_dashboard and "dashboard" not in resolved_groups:
        resolved_groups.append("dashboard")

    return {
        "resolvedGroups": resolved_groups,
        "inspectionGroup": base_group,
        "includeInConditionScoring": True,
        "groupMismatch": base_group != declared_group,
        "groupWarning": (
            f"Anh duoc gui o nhom {declared_group} nhung he thong da resolve thanh {base_group}."
            if base_group != declared_group
            else None
        ),
    }


def build_coverage(assets: list[ProcessedImageAsset]) -> tuple[list[str], list[str], list[str]]:
    covered = set()
    partial = set()
    inspection = set()
    for asset in assets:
        if asset.inspection_group:
            inspection.add(asset.inspection_group)
        for group in asset.resolved_groups:
            if group == "dashboard" and asset.inspection_group == "interior_front":
                partial.add(group)
                continue
            if group in GROUPS and group != "document":
                covered.add(group)
    return sorted(covered), sorted(partial - covered), sorted(inspection)


def infer_group_from_path(public_id: str, url: str) -> str:
    haystack = f"{public_id} {url}".lower()
    if any(token in haystack for token in ["document", "giay_to", "dang_kiem", "registration"]):
        return "document"
    if any(token in haystack for token in ["interior_front", "noi_that_truoc", "taplo", "dashboard"]):
        return "interior_front" if "dashboard" not in haystack else "dashboard"
    if any(token in haystack for token in ["interior_rear", "noi_that_sau"]):
        return "interior_rear"
    if any(token in haystack for token in ["duoi_xe", "rear", "sau"]):
        return "rear"
    if any(token in haystack for token in ["front", "truoc"]):
        return "front"
    if "left_side" in haystack or "trai" in haystack:
        return "left_side"
    if "right_side" in haystack or "phai" in haystack:
        return "right_side"
    if "engine" in haystack or "khoang_may" in haystack or "may" in haystack:
        return "engine_bay"
    if "odo" in haystack or "odometer" in haystack:
        return "odometer"
    if "damage" in haystack or "xuoc" in haystack or "mop" in haystack:
        return "damage_detail"
    return "other"


def parse_caption(caption: str | None) -> dict[str, Any]:
    text = (caption or "").strip().lower()
    if not text:
        return {"captionHintGroup": "other", "captionClaims": []}

    hint_group = "other"
    claims: list[dict[str, Any]] = []

    if any(token in text for token in ["giay to", "dang kiem", "ca vet", "registration", "document"]):
        hint_group = "document"
    elif any(token in text for token in ["khoang may", "may xe", "engine"]):
        hint_group = "engine_bay"
    elif any(token in text for token in ["odo", "dong ho"]):
        hint_group = "odometer"
    elif any(token in text for token in ["noi that sau", "ghe sau", "interior rear"]):
        hint_group = "interior_rear"
    elif any(token in text for token in ["noi that truoc", "tap lo", "vo lang", "dashboard", "interior front"]):
        hint_group = "interior_front"
    elif any(token in text for token in ["duoi xe", "can sau", "rear"]):
        hint_group = "rear"
    elif any(token in text for token in ["dau xe", "can truoc", "front"]):
        hint_group = "front"

    issue = None
    if "xuoc" in text:
        issue = "scratch"
    elif "mop" in text:
        issue = "dent"
    elif "son lai" in text:
        issue = "possible_repaint"

    if issue:
        claims.append(
            {
                "type": "damage_claim",
                "issue": issue,
                "location": hint_group if hint_group != "other" else None,
                "severity": "minor" if "nhe" in text else None,
                "text": caption,
            }
        )

    return {"captionHintGroup": hint_group, "captionClaims": claims}


def confidence_for_hint(group: str) -> float:
    return 0.85 if group not in {"other"} else 0.35


def compute_perceptual_hash(url: str) -> str | None:
    try:
        thumb_url = build_thumbnail_url(url)
        request = Request(thumb_url, headers={"User-Agent": "rag-chatbot-pricing/1.0"})
        with urlopen(request, timeout=max(1, get_settings().PRICING_IMAGE_HASH_TIMEOUT_SECONDS)) as response:
            raw = response.read()
        image = Image.open(io.BytesIO(raw)).convert("L").resize((9, 8))
        pixels = list(image.getdata())
        rows = [pixels[idx:idx + 9] for idx in range(0, len(pixels), 9)]
        bits = []
        for row in rows:
            for index in range(8):
                bits.append("1" if row[index] > row[index + 1] else "0")
        return "".join(bits)
    except Exception:
        return None


def build_thumbnail_url(url: str) -> str:
    parsed = urlparse(url)
    marker = "/upload/"
    if marker not in parsed.path:
        return url
    prefix, suffix = parsed.path.split(marker, 1)
    transformed = f"{prefix}{marker}w_64,h_64,c_fill,q_auto,f_auto/{suffix}"
    return urlunparse((parsed.scheme, parsed.netloc, transformed, parsed.params, parsed.query, parsed.fragment))


def hamming_distance(left: str, right: str) -> int:
    if len(left) != len(right):
        return max(len(left), len(right))
    return sum(1 for lch, rch in zip(left, right) if lch != rch)
