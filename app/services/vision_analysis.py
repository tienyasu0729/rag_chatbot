"""
Phan tich tinh trang xe bang Beeknoee Chat Completions vision.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.services.image_processor import ProcessedImageBundle
from app.services.llm import _extract_json_object

logger = logging.getLogger(__name__)


def analyze_vehicle_condition(bundle: ProcessedImageBundle) -> dict[str, Any]:
    if not bundle.payload_images:
        return _default_assessment("Khong co anh hop le de phan tich, dung danh gia mac dinh")

    settings = get_settings()
    if not settings.VISION_API_KEY.strip():
        logger.warning("VISION_API_KEY chua duoc cau hinh, dung assessment mac dinh")
        return _default_assessment("Khong cau hinh VISION_API_KEY, dung danh gia mac dinh")
    if not settings.VISION_MODEL.strip():
        logger.warning("VISION_MODEL chua duoc cau hinh, dung assessment mac dinh")
        return _default_assessment("Khong cau hinh VISION_MODEL, dung danh gia mac dinh")

    prompt = """
Ban la chuyen vien tham dinh xe da qua su dung. Hay danh gia tinh trang ky thuat thuc te tu anh.
Chi tra ve DUY NHAT 1 JSON object hop le, khong markdown, khong giai thich.

Schema bat buoc:
{
  "condition_score": 0,
  "score_breakdown": {
    "paint_exterior": 0,
    "body_damage": 0,
    "interior": 0,
    "mechanical_visible": 0,
    "tires_wheels": 0
  },
  "damage_percentage": {
    "scratch": "~15%" hoac "unknown",
    "dent": "~3%" hoac "unknown"
  },
  "repaint_detected": "mo ta ngan",
  "glass_lights_mirrors": "mo ta ngan",
  "seat_wear": "moi | binh thuong | mon nhieu | rach",
  "dashboard_steering": "mo ta ngan",
  "flood_signs": "co | khong | nghi ngo",
  "risk_flags": ["canh bao 1", "canh bao 2"],
  "damage_summary": "tom tat ngan cho manager"
}

Uu tien canh bao cu the: son lai, dau vet tai nan, mon ghe, nghi ngap nuoc, hu hong kinh den guong.
Neu anh khong the ket luan chac chan, ghi ro muc do nghi ngo.
""".strip()

    try:
        client = OpenAI(
            api_key=settings.VISION_API_KEY.strip(),
            base_url=settings.VISION_BASE_URL.strip() or "https://platform.beeknoee.com/api/v1",
        )

        content: list[dict[str, Any]] = [
            {"type": "text", "text": prompt},
        ]

        for item in bundle.payload_images:
            encoded = base64.b64encode(item.data).decode("utf-8")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{item.mime_type};base64,{encoded}",
                    },
                }
            )

        response = client.chat.completions.create(
            model=settings.VISION_MODEL.strip(),
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        raw_text = (response.choices[0].message.content or "").strip()
        payload = json.loads(_extract_json_object(raw_text))
        if not isinstance(payload, dict):
            raise ValueError("Beeknoee vision khong tra ve JSON object")
        return _normalize_assessment(payload)
    except Exception:
        logger.exception("Beeknoee vision phan tich that bai, dung assessment mac dinh")
        return _default_assessment(
            "Khong phan tich duoc anh tu Beeknoee, dung danh gia mac dinh"
        )


def _normalize_assessment(payload: dict[str, Any]) -> dict[str, Any]:
    default = _default_assessment("")
    default_breakdown = default["score_breakdown"]
    payload_breakdown = payload.get("score_breakdown") if isinstance(payload.get("score_breakdown"), dict) else {}

    breakdown = {
        "paint_exterior": _clamp_int(payload_breakdown.get("paint_exterior"), 0, 25, default_breakdown["paint_exterior"]),
        "body_damage": _clamp_int(payload_breakdown.get("body_damage"), 0, 25, default_breakdown["body_damage"]),
        "interior": _clamp_int(payload_breakdown.get("interior"), 0, 25, default_breakdown["interior"]),
        "mechanical_visible": _clamp_int(payload_breakdown.get("mechanical_visible"), 0, 15, default_breakdown["mechanical_visible"]),
        "tires_wheels": _clamp_int(payload_breakdown.get("tires_wheels"), 0, 10, default_breakdown["tires_wheels"]),
    }

    computed_score = sum(breakdown.values())
    condition_score = _clamp_int(payload.get("condition_score"), 0, 100, computed_score)

    damage_percentage = payload.get("damage_percentage") if isinstance(payload.get("damage_percentage"), dict) else {}
    risk_flags = payload.get("risk_flags")
    if not isinstance(risk_flags, list):
        risk_flags = default["risk_flags"].copy()
    risk_flags = [str(flag).strip() for flag in risk_flags if str(flag).strip()]

    damage_summary = str(payload.get("damage_summary") or "").strip()
    if not damage_summary:
        damage_summary = default["damage_summary"]

    return {
        "condition_score": condition_score,
        "score_breakdown": breakdown,
        "damage_percentage": {
            "scratch": _normalize_text_field(damage_percentage.get("scratch"), default["damage_percentage"]["scratch"]),
            "dent": _normalize_text_field(damage_percentage.get("dent"), default["damage_percentage"]["dent"]),
        },
        "repaint_detected": _normalize_text_field(payload.get("repaint_detected"), "Khong ro"),
        "glass_lights_mirrors": _normalize_text_field(payload.get("glass_lights_mirrors"), "Khong ro"),
        "seat_wear": _normalize_text_field(payload.get("seat_wear"), "Khong ro"),
        "dashboard_steering": _normalize_text_field(payload.get("dashboard_steering"), "Khong ro"),
        "flood_signs": _normalize_text_field(payload.get("flood_signs"), "Khong ro"),
        "risk_flags": risk_flags,
        "damage_summary": damage_summary,
    }


def _default_assessment(reason: str) -> dict[str, Any]:
    risk_flags = [reason] if reason else []
    return {
        "condition_score": 60,
        "score_breakdown": {
            "paint_exterior": 15,
            "body_damage": 15,
            "interior": 15,
            "mechanical_visible": 9,
            "tires_wheels": 6,
        },
        "damage_percentage": {
            "scratch": "unknown",
            "dent": "unknown",
        },
        "repaint_detected": "Khong ro",
        "glass_lights_mirrors": "Khong ro",
        "seat_wear": "Khong ro",
        "dashboard_steering": "Khong ro",
        "flood_signs": "Khong ro",
        "risk_flags": risk_flags,
        "damage_summary": (
            "Khong doc duoc anh hoac phan tich vision that bai; "
            "dang dung danh gia mac dinh nen do tin cay gia de xuat thap hon."
        ),
    }


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, parsed))


def _normalize_text_field(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text or default
