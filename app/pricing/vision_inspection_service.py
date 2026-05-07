"""
Vision inspection service cho anh URL-based.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from app.config import get_settings

VALID_GROUPS = {
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
    "other",
}
VALID_QUALITY = {"good", "acceptable", "blurry", "invalid"}


def inspect_vehicle_images(processed: dict[str, Any], vehicle_input: dict[str, Any]) -> dict[str, Any]:
    groups = defaultdict(list)
    for asset in processed["acceptedAssets"]:
        if not asset.include_in_condition_scoring or not asset.inspection_group:
            continue
        groups[asset.inspection_group].append(asset)

    inspection_groups: dict[str, Any] = {}
    damage_findings: list[dict[str, Any]] = []
    risk_flags: list[dict[str, Any]] = []
    raw_model_outputs: list[dict[str, Any]] = []

    for group_name, assets in groups.items():
        raw_payload = inspect_group(group_name, assets)
        raw_model_outputs.append({"group": group_name, "payload": raw_payload})
        inspection = sanitize_group_inspection(group_name, assets, raw_payload)
        inspection_groups[group_name] = inspection
        damage_findings.extend(inspection.get("findings", []))
        risk_flags.extend(inspection.get("riskFlags", []))

    return {
        "inspectionGroups": inspection_groups,
        "damageFindings": damage_findings,
        "riskFlags": risk_flags,
        "rawModelOutputs": raw_model_outputs,
        "sanitizedInspection": inspection_groups,
    }


def inspect_group(group_name: str, assets: list[Any]) -> dict[str, Any]:
    settings = get_settings()
    if settings.VISION_API_KEY.strip() and settings.VISION_MODEL.strip():
        try:
            return inspect_group_with_model(group_name, assets)
        except Exception:
            pass
    return heuristic_group_inspection(group_name, assets)


def inspect_group_with_model(group_name: str, assets: list[Any]) -> dict[str, Any]:
    from openai import OpenAI
    from app.services.llm import _extract_json_object

    settings = get_settings()
    client = OpenAI(
        api_key=settings.VISION_API_KEY.strip(),
        base_url=settings.VISION_BASE_URL.strip() or "https://platform.beeknoee.com/api/v1",
    )
    allowed_public_ids = [asset.public_id for asset in assets]
    prompt = (
        "Ban la chuyen vien inspection xe cu. "
        "Chi danh gia dau hieu nhin thay duoc tu anh. "
        "Xe sach hoac anh binh thuong khong bat buoc phai co findings. "
        "Khong duoc tao scratch, dent, wear chi de lap schema. "
        "Khong duoc dung watermark, bong do, phan chieu, bui nhe, anh mo de ket luan tray xuoc, mop, son lai. "
        "Khong ket luan tai nan, ngap nuoc, tua ODO, loi may hop so tu anh thong thuong. "
        "possible_repaint chi duoc tra ve neu thay ro lech mau panel, khe ho, hoac dau hieu son lai ro rang. "
        f"evidenceImages chi duoc chon tu danh sach publicId nay: {allowed_public_ids}. "
        "Tra ve duy nhat JSON hop le theo schema: "
        "{"
        "\"detectedGroup\":\"front|rear|left_side|right_side|interior_front|interior_rear|dashboard|odometer|engine_bay|tire|damage_detail|other\","
        "\"imageQuality\":\"good|acceptable|blurry|invalid\","
        "\"score\":75,"
        "\"confidence\":0.7,"
        "\"findings\":[],"
        "\"riskFlags\":[]"
        "}"
    )
    content = [{"type": "text", "text": prompt}]
    for asset in assets[:4]:
        caption_text = str(getattr(asset, "caption", "") or "").strip()
        if caption_text:
            content.append(
                {
                    "type": "text",
                    "text": f"Caption cho {asset.public_id}: {caption_text}. Caption chi la goi y cua nguoi dung, co the sai.",
                }
            )
        content.append({"type": "image_url", "image_url": {"url": asset.url}})
    response = client.chat.completions.create(
        model=settings.VISION_MODEL.strip(),
        messages=[{"role": "user", "content": content}],
        temperature=0.0,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )
    raw = (response.choices[0].message.content or "").strip()
    return json.loads(_extract_json_object(raw))


def heuristic_group_inspection(group_name: str, assets: list[Any]) -> dict[str, Any]:
    score_map = {
        "front": 78,
        "rear": 77,
        "left_side": 76,
        "right_side": 76,
        "interior_front": 74,
        "interior_rear": 75,
        "dashboard": 72,
        "odometer": 72,
        "engine_bay": 70,
        "tire": 71,
        "damage_detail": 65,
        "other": 68,
    }
    risk_flags = []
    if group_name == "engine_bay":
        risk_flags.append(
            {
                "type": "requires_engine_bay_inspection",
                "severity": "low",
                "message": "Khoang may can kiem tra thuc te them truoc khi chot gia.",
            }
        )
    return {
        "detectedGroup": group_name,
        "imageQuality": "acceptable",
        "score": score_map.get(group_name, 70),
        "confidence": 0.55,
        "findings": [],
        "riskFlags": risk_flags,
    }


def sanitize_group_inspection(group_name: str, assets: list[Any], payload: dict[str, Any]) -> dict[str, Any]:
    allowed_public_ids = {asset.public_id for asset in assets}
    raw_detected_group = str(payload.get("detectedGroup") or "").strip()
    raw_image_quality = str(payload.get("imageQuality") or "").strip().lower()
    valid_output = True
    warning = None
    detected_group = raw_detected_group if raw_detected_group in VALID_GROUPS else None
    image_quality = raw_image_quality if raw_image_quality in VALID_QUALITY else "unknown"
    if detected_group is None or image_quality == "unknown":
        valid_output = False
        warning = "Vision output khong hop le; chi dung declaredGroup/filenameHint cho coverage."

    findings = []
    for finding in payload.get("findings", []) if isinstance(payload.get("findings"), list) else []:
        if not isinstance(finding, dict):
            continue
        issue = str(finding.get("issue") or "").strip() or "requires_inspection"
        confidence = max(0.0, min(1.0, float(finding.get("confidence") or 0.0)))
        if confidence < 0.65:
            continue
        if issue in {"possible_repaint", "structural_damage", "accident_damage"} and confidence < 0.75:
            continue
        evidence = [str(item).strip() for item in (finding.get("evidenceImages") or []) if str(item).strip()]
        evidence = [item for item in evidence if item in allowed_public_ids]
        if not evidence:
            placeholder = str((finding.get("evidenceImages") or [""])[0]).strip().lower()
            if placeholder in {"public_id", "publicid", "public-id"} and assets:
                evidence = [assets[0].public_id]
        if not evidence:
            continue
        findings.append(
            {
                "issue": issue,
                "label": str(finding.get("label") or "Can kiem tra thuc te").strip(),
                "location": str(finding.get("location") or group_name).strip(),
                "severity": normalize_severity(finding.get("severity")),
                "confidence": confidence,
                "evidenceImages": evidence,
            }
        )

    risk_flags = []
    for flag in payload.get("riskFlags", []) if isinstance(payload.get("riskFlags"), list) else []:
        if not isinstance(flag, dict):
            continue
        risk_flags.append(
            {
                "type": str(flag.get("type") or "requires_inspection").strip(),
                "severity": normalize_severity(flag.get("severity")),
                "message": str(flag.get("message") or "Can kiem tra thuc te.").strip(),
            }
        )

    return {
        "declaredGroup": group_name,
        "detectedGroup": detected_group,
        "imageQuality": image_quality,
        "score": int(payload.get("score") or 70),
        "confidence": max(0.0, min(1.0, float(payload.get("confidence") or 0.55))),
        "findings": findings if valid_output else [],
        "riskFlags": risk_flags,
        "groupMismatch": bool(detected_group and detected_group != group_name),
        "validVisionOutput": valid_output,
        "usedForCoverage": True,
        "usedForConditionScoring": valid_output,
        "warning": warning,
    }


def normalize_severity(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"minor", "medium", "major", "critical"}:
        return text
    if text == "moderate":
        return "medium"
    return "minor"
