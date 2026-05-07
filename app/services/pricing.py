"""
Truy van gia thi truong va tinh gia nhap de xuat.
"""

from __future__ import annotations

import json
import logging
import math
import unicodedata
from typing import Any

from app.db import sqlserver
from app.services.llm import json_completion

logger = logging.getLogger(__name__)


def _get_market_data(
    *,
    subcategory_id: int | None = None,
    subcategory_name: str | None = None,
    year: int | None = None,
    fuel: str | None = None,
    transmission: str | None = None,
    origin: str | None = None,
) -> dict[str, Any]:
    cte_sql, params = _build_market_cte(
        subcategory_id=subcategory_id,
        subcategory_name=subcategory_name,
        year=year,
        fuel=fuel,
        transmission=transmission,
        origin=origin,
    )

    aggregate_sql = f"""
WITH candidate_matches AS (
    {cte_sql}
),
ranked_matches AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY priority_match) AS match_rank
    FROM candidate_matches
),
deduped AS (
    SELECT * FROM ranked_matches WHERE match_rank = 1
)
SELECT
    COUNT(*) AS comparable_count,
    MIN(price) AS market_min,
    AVG(CAST(price AS FLOAT)) AS market_avg,
    MAX(price) AS market_max
FROM deduped
WHERE price IS NOT NULL
"""

    comparables_sql = f"""
WITH candidate_matches AS (
    {cte_sql}
),
ranked_matches AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY priority_match) AS match_rank
    FROM candidate_matches
),
deduped AS (
    SELECT * FROM ranked_matches WHERE match_rank = 1
)
SELECT TOP 10
    id,
    title,
    price,
    year,
    fuel,
    transmission,
    origin,
    status,
    created_at,
    priority_match
FROM deduped
ORDER BY priority_match ASC, created_at DESC
"""

    aggregate_rows = sqlserver.query_positional_readonly(aggregate_sql, params=params)
    aggregate = aggregate_rows[0] if aggregate_rows else {}
    comparable_rows = sqlserver.query_positional_readonly(comparables_sql, params=params)

    return {
        "market_min": _to_int_or_none(aggregate.get("market_min")),
        "market_avg": _to_int_or_none(aggregate.get("market_avg")),
        "market_max": _to_int_or_none(aggregate.get("market_max")),
        "comparable_count": int(aggregate.get("comparable_count") or 0),
        "comparables": [_serialize_comparable(row) for row in comparable_rows],
    }


def estimate_purchase_price(
    *,
    market_data: dict[str, Any],
    vehicle_assessment: dict[str, Any],
    vehicle_config: dict[str, Any],
) -> dict[str, Any]:
    schema_hint = json.dumps(
        {
            "suggested_purchase_price": 0,
            "price_range_min": 0,
            "price_range_max": 0,
            "market_avg": 0,
            "market_min": 0,
            "market_max": 0,
            "comparable_count": 0,
            "condition_score": 0,
            "damage_summary": "",
            "risk_flags": [],
            "deduction_factors": [],
        },
        ensure_ascii=False,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ban la chuyen gia dinh gia nhap xe cu cho showroom. "
                "Muc tieu la de xuat gia nhap du an toan de con bien loi nhuan, "
                "khong viet van ban hang."
            ),
        },
        {
            "role": "user",
            "content": (
                "Hay tra ve JSON dinh gia nhap xe dua tren du lieu thi truong va tham dinh ky thuat.\n"
                f"vehicle_config={json.dumps(vehicle_config, ensure_ascii=False)}\n"
                f"market_data={json.dumps(market_data, ensure_ascii=False)}\n"
                f"vehicle_assessment={json.dumps(vehicle_assessment, ensure_ascii=False)}"
            ),
        },
    ]

    try:
        payload = json_completion(
            messages=messages,
            schema_hint=schema_hint,
            temperature=0.1,
            max_tokens=1200,
        )
        return _normalize_pricing_payload(payload, market_data, vehicle_assessment)
    except Exception:
        logger.exception("LLM dinh gia that bai, dung cong thuc fallback")
        return _fallback_pricing(market_data, vehicle_assessment)


def _build_market_cte(
    *,
    subcategory_id: int | None,
    subcategory_name: str | None,
    year: int | None,
    fuel: str | None,
    transmission: str | None,
    origin: str | None,
) -> tuple[str, list[Any]]:
    common_filters = [
        "v.is_deleted = 0",
        "v.status IN ('Available', 'Sold', 'Reserved')",
    ]
    common_params: list[Any] = []

    if year is not None:
        common_filters.append("v.year BETWEEN ? AND ?")
        common_params.extend([year - 2, year + 2])

    if fuel:
        common_filters.append("v.fuel = ?")
        common_params.append(fuel.strip())

    if transmission:
        common_filters.append("v.transmission = ?")
        common_params.append(transmission.strip())

    if origin:
        common_filters.append("v.origin = ?")
        common_params.append(origin.strip())

    where_prefix = " AND ".join(common_filters)
    base_select = f"""
SELECT
    v.id,
    v.title,
    v.price,
    v.year,
    v.fuel,
    v.transmission,
    v.origin,
    v.status,
    v.created_at,
    {{priority}} AS priority_match
FROM Vehicles v
JOIN Subcategories sc ON v.subcategory_id = sc.id
WHERE {where_prefix} AND {{predicate}}
""".strip()

    branches: list[str] = []
    params: list[Any] = []

    if subcategory_id is not None:
        branches.append(base_select.format(priority=1, predicate="v.subcategory_id = ?"))
        params.extend(common_params)
        params.append(subcategory_id)
    else:
        lookup = (subcategory_name or "").strip()
        normalized = _normalize_lookup_text(lookup)
        if not lookup:
            raise ValueError("Khong the truy van market data neu thieu subcategory_name")

        branches.extend(
            [
                base_select.format(priority=2, predicate="sc.name = ?"),
                base_select.format(priority=3, predicate="sc.name_normalized = ?"),
                base_select.format(priority=4, predicate="sc.name LIKE ?"),
                base_select.format(priority=5, predicate="sc.name_normalized LIKE ?"),
            ]
        )
        params.extend(common_params + [lookup])
        params.extend(common_params + [normalized])
        params.extend(common_params + [f"%{lookup}%"])
        params.extend(common_params + [f"%{normalized}%"])

    return "\nUNION ALL\n".join(branches), params


def _normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def _normalize_pricing_payload(
    payload: dict[str, Any],
    market_data: dict[str, Any],
    vehicle_assessment: dict[str, Any],
) -> dict[str, Any]:
    fallback = _fallback_pricing(market_data, vehicle_assessment)
    market_avg = market_data.get("market_avg") or 0
    market_min = market_data.get("market_min") or 0
    market_max = market_data.get("market_max") or 0
    comparable_count = market_data.get("comparable_count") or 0

    suggested = _to_non_negative_int(payload.get("suggested_purchase_price"), fallback["suggested_purchase_price"])
    price_range_min = _to_non_negative_int(payload.get("price_range_min"), fallback["price_range_min"])
    price_range_max = _to_non_negative_int(payload.get("price_range_max"), fallback["price_range_max"])
    if price_range_max < price_range_min:
        price_range_min, price_range_max = price_range_max, price_range_min

    deduction_factors = payload.get("deduction_factors")
    if not isinstance(deduction_factors, list):
        deduction_factors = fallback["deduction_factors"]
    deduction_factors = [str(item).strip() for item in deduction_factors if str(item).strip()]

    return {
        "suggested_purchase_price": suggested,
        "price_range_min": price_range_min,
        "price_range_max": price_range_max,
        "market_avg": _to_non_negative_int(payload.get("market_avg"), market_avg),
        "market_min": _to_non_negative_int(payload.get("market_min"), market_min),
        "market_max": _to_non_negative_int(payload.get("market_max"), market_max),
        "comparable_count": _to_non_negative_int(payload.get("comparable_count"), comparable_count),
        "condition_score": _to_non_negative_int(
            payload.get("condition_score"),
            int(vehicle_assessment.get("condition_score") or 0),
        ),
        "damage_summary": str(payload.get("damage_summary") or vehicle_assessment.get("damage_summary") or "").strip(),
        "risk_flags": _normalize_str_list(payload.get("risk_flags"), vehicle_assessment.get("risk_flags")),
        "deduction_factors": deduction_factors,
    }


def _fallback_pricing(
    market_data: dict[str, Any],
    vehicle_assessment: dict[str, Any],
) -> dict[str, Any]:
    avg_market = market_data.get("market_avg") or 0
    condition_score = int(vehicle_assessment.get("condition_score") or 0)
    suggested = int(avg_market * (condition_score / 100) * 0.85) if avg_market else 0
    price_range_min = int(suggested * 0.95) if suggested else 0
    price_range_max = int(suggested * 1.05) if suggested else 0

    return {
        "suggested_purchase_price": suggested,
        "price_range_min": price_range_min,
        "price_range_max": price_range_max,
        "market_avg": _to_int_or_none(avg_market) or 0,
        "market_min": _to_int_or_none(market_data.get("market_min")) or 0,
        "market_max": _to_int_or_none(market_data.get("market_max")) or 0,
        "comparable_count": int(market_data.get("comparable_count") or 0),
        "condition_score": condition_score,
        "damage_summary": str(vehicle_assessment.get("damage_summary") or "").strip(),
        "risk_flags": _normalize_str_list(vehicle_assessment.get("risk_flags"), []),
        "deduction_factors": [
            (
                f"Fallback cong thuc: avg_market x ({condition_score}/100) x 0.85 = {suggested:,} VND"
                if suggested
                else "Khong du du lieu thi truong de tinh fallback co nghia"
            )
        ],
    }


def _serialize_comparable(row: dict[str, Any]) -> dict[str, Any]:
    created_at = row.get("created_at")
    created_at_text = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at or "")
    return {
        "id": int(row["id"]),
        "title": str(row.get("title") or ""),
        "price": _to_int_or_none(row.get("price")),
        "year": int(row["year"]) if row.get("year") is not None else None,
        "fuel": row.get("fuel"),
        "transmission": row.get("transmission"),
        "origin": row.get("origin"),
        "status": str(row.get("status") or ""),
        "created_at": created_at_text or None,
        "priority_match": int(row.get("priority_match") or 0),
    }


def _normalize_str_list(value: Any, default: Any) -> list[str]:
    items = value if isinstance(value, list) else default if isinstance(default, list) else []
    return [str(item).strip() for item in items if str(item).strip()]


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(math.floor(float(value)))
    except (TypeError, ValueError):
        return None


def _to_non_negative_int(value: Any, default: int) -> int:
    parsed = _to_int_or_none(value)
    if parsed is None:
        return default
    return max(0, parsed)
