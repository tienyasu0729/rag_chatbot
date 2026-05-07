"""
Trích xuất structured preferences từ lịch sử hội thoại.
Gọi LLM 1 lần duy nhất khi intent là RECOMMEND/CLARIFY.
"""

import json
import logging

from app.db import sqlserver
from app.services.llm import chat_completion

logger = logging.getLogger(__name__)

PREFERENCE_SCHEMA = {
    "ngan_sach_min": None,
    "ngan_sach_max": None,
    "muc_dich": None,
    "nhien_lieu": None,
    "so_cho": None,
    "hop_so": None,
    "hang_xe_yeu_thich": [],
    "hang_xe_khong_thich": [],
    "uu_tien": None,
}

# Cached valid values from DB registry tables
_valid_fuels: list[str] | None = None
_valid_transmissions: list[str] | None = None


def _load_registry_values():
    """Query VehicleFuelTypes and VehicleTransmissions once, cache in module."""
    global _valid_fuels, _valid_transmissions

    if _valid_fuels is None:
        try:
            rows = sqlserver.query("SELECT name FROM VehicleFuelTypes WHERE status = 'active'")
            _valid_fuels = [r["name"] for r in rows]
        except Exception:
            _valid_fuels = ["Xăng", "Dầu", "Điện", "Hybrid"]
            logger.warning("Failed to load VehicleFuelTypes, using defaults")

    if _valid_transmissions is None:
        try:
            rows = sqlserver.query("SELECT name FROM VehicleTransmissions WHERE status = 'active'")
            _valid_transmissions = [r["name"] for r in rows]
        except Exception:
            _valid_transmissions = ["Số sàn", "Tự động"]
            logger.warning("Failed to load VehicleTransmissions, using defaults")


def _build_extract_prompt(messages_text: str) -> str:
    _load_registry_values()

    fuels_str = ", ".join(f'"{f}"' for f in _valid_fuels)
    trans_str = ", ".join(f'"{t}"' for t in _valid_transmissions)

    return f"""Trích xuất thông tin nhu cầu mua xe từ hội thoại bên dưới.
Chỉ điền các field có thông tin rõ ràng từ lời khách nói. Không suy đoán.

Quy tắc:
- ngan_sach_min/max: đơn vị VND ĐẦY ĐỦ. Ví dụ: "500 triệu" = 500000000, "1 tỷ" = 1000000000
- nhien_lieu: PHẢI là 1 trong [{fuels_str}], hoặc null
- hop_so: PHẢI là 1 trong [{trans_str}], hoặc null
- muc_dich: "gia_dinh" | "ca_nhan" | "kinh_doanh" | null
- uu_tien: "tiet_kiem" | "manh_me" | "tien_nghi" | "gia_tot" | null
- so_cho: số nguyên (4, 5, 7) hoặc null
- hang_xe_yeu_thich / hang_xe_khong_thich: list tên hãng xe, hoặc []

Trả về ĐÚNG JSON, field không biết để null. Không giải thích gì thêm.
{{"ngan_sach_min": null, "ngan_sach_max": null, "muc_dich": null, "nhien_lieu": null, "so_cho": null, "hop_so": null, "hang_xe_yeu_thich": [], "hang_xe_khong_thich": [], "uu_tien": null}}

Hội thoại:
{messages_text}"""


def extract_preferences(history: list[dict], current_message: str) -> dict:
    """
    Trích xuất preferences từ history + tin nhắn hiện tại.
    Gọi LLM 1 lần, trả về dict theo PREFERENCE_SCHEMA.
    """
    lines = []
    for msg in history[-6:]:
        role = "Khách" if msg["role"] == "user" else "Tư vấn viên"
        lines.append(f"{role}: {msg['content']}")
    lines.append(f"Khách: {current_message}")
    messages_text = "\n".join(lines)

    prompt = _build_extract_prompt(messages_text)

    try:
        response = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300,
        )

        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        data = json.loads(cleaned)

        result = {}
        for key in PREFERENCE_SCHEMA:
            val = data.get(key)
            if val is not None and val != [] and val != "":
                result[key] = val

        return result

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Preference extraction parse error: %s", e)
        return {}
    except Exception:
        logger.exception("Preference extraction failed")
        return {}


def merge_preferences(existing: dict, new_extracted: dict) -> dict:
    """Merge new preferences into existing — non-None values overwrite."""
    merged = dict(existing) if existing else {}
    for key, val in new_extracted.items():
        if val is not None and val != [] and val != "":
            merged[key] = val
        elif key not in merged:
            merged[key] = PREFERENCE_SCHEMA.get(key)
    return merged


def format_preferences_summary(prefs: dict) -> str:
    """Chuyển preferences dict thành mô tả tiếng Việt cho prompt."""
    if not prefs:
        return "(Chưa có thông tin nhu cầu)"

    parts = []
    if prefs.get("ngan_sach_min") or prefs.get("ngan_sach_max"):
        min_b = f"{prefs['ngan_sach_min']/1e6:.0f} triệu" if prefs.get("ngan_sach_min") else "?"
        max_b = f"{prefs['ngan_sach_max']/1e6:.0f} triệu" if prefs.get("ngan_sach_max") else "?"
        parts.append(f"Ngân sách: {min_b} - {max_b} VNĐ")
    if prefs.get("muc_dich"):
        labels = {"gia_dinh": "Gia đình", "ca_nhan": "Cá nhân", "kinh_doanh": "Kinh doanh"}
        parts.append(f"Mục đích: {labels.get(prefs['muc_dich'], prefs['muc_dich'])}")
    if prefs.get("nhien_lieu"):
        parts.append(f"Nhiên liệu: {prefs['nhien_lieu']}")
    if prefs.get("hop_so"):
        parts.append(f"Hộp số: {prefs['hop_so']}")
    if prefs.get("so_cho"):
        parts.append(f"Số chỗ: {prefs['so_cho']}")
    if prefs.get("uu_tien"):
        labels = {"tiet_kiem": "Tiết kiệm", "manh_me": "Mạnh mẽ", "tien_nghi": "Tiện nghi", "gia_tot": "Giá tốt"}
        parts.append(f"Ưu tiên: {labels.get(prefs['uu_tien'], prefs['uu_tien'])}")
    if prefs.get("hang_xe_yeu_thich"):
        parts.append(f"Thích: {', '.join(prefs['hang_xe_yeu_thich'])}")
    if prefs.get("hang_xe_khong_thich"):
        parts.append(f"Không thích: {', '.join(prefs['hang_xe_khong_thich'])}")

    return "\n".join(parts) if parts else "(Chưa có thông tin nhu cầu)"
