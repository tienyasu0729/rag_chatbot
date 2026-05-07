"""
Pricing-only SQL tools. Khong dung cho chatbot dispatcher.
"""

from __future__ import annotations

from typing import Any

from app.db import sqlserver


def pricing_validate_reference_data(*, category_id: int, subcategory_id: int) -> dict[str, Any]:
    strict_sql = """
SELECT
    c.id AS category_id,
    sc.id AS subcategory_id,
    c.name AS category_name,
    sc.name AS subcategory_name
FROM Categories c
JOIN Subcategories sc ON sc.category_id = c.id
WHERE c.id = ? AND sc.id = ?
"""
    fallback_sql = """
SELECT
    c.id AS category_id,
    sc.id AS subcategory_id,
    c.name AS category_name,
    sc.name AS subcategory_name
FROM Categories c
JOIN Subcategories sc ON sc.id = ?
WHERE c.id = ?
"""
    try:
        rows = sqlserver.query_positional_readonly(strict_sql, params=[category_id, subcategory_id])
    except Exception:
        rows = sqlserver.query_positional_readonly(fallback_sql, params=[subcategory_id, category_id])
    return {"valid": bool(rows), "item": rows[0] if rows else None}


def pricing_get_market_candidates(
    *,
    limit: int = 150,
    category_id: int,
    subcategory_id: int | None,
    exclude_vehicle_id: int | None = None,
    year: int | None = None,
    year_range: int = 2,
    model_keyword: str | None = None,
    market_window_days: int = 90,
) -> dict[str, Any]:
    top_n = max(1, min(int(limit), 500))
    conditions = [
        "v.is_deleted = 0",
        "v.price IS NOT NULL",
        "v.price > 0",
        "v.category_id = ?",
        "v.status IN ('Available', 'Sold', 'Reserved')",
    ]
    params: list[Any] = [category_id]

    if subcategory_id is not None:
        conditions.append("v.subcategory_id = ?")
        params.append(subcategory_id)
    if exclude_vehicle_id is not None:
        conditions.append("v.id <> ?")
        params.append(exclude_vehicle_id)
    if year is not None:
        conditions.append("v.year BETWEEN ? AND ?")
        params.extend([year - year_range, year + year_range])
    if model_keyword:
        conditions.append("LOWER(v.title) LIKE ?")
        params.append(f"%{str(model_keyword).strip().lower()}%")
    if market_window_days > 0:
        conditions.append("COALESCE(CAST(v.posting_date AS date), CAST(v.created_at AS date)) >= DATEADD(DAY, ?, CAST(GETDATE() AS date))")
        params.append(-abs(int(market_window_days)))

    where = " AND ".join(conditions)
    sql = f"""
SELECT TOP {top_n}
    CAST(v.id AS varchar(50)) AS listingId,
    v.id AS vehicleId,
    v.category_id AS categoryId,
    v.subcategory_id AS subcategoryId,
    v.title,
    CAST(v.price AS bigint) AS price,
    v.year,
    v.mileage,
    v.fuel,
    v.transmission,
    v.body_style AS bodyStyle,
    v.origin,
    v.branch_id AS branchId,
    v.status,
    CONVERT(varchar(10), COALESCE(CAST(v.posting_date AS date), CAST(v.created_at AS date)), 23) AS postingDate
FROM Vehicles v
WHERE {where}
ORDER BY COALESCE(v.posting_date, v.created_at) DESC, v.id DESC
"""
    items = sqlserver.query_positional_readonly(sql, params=params)
    return {"items": items, "count": len(items)}


def pricing_get_segment_candidates(
    *,
    limit: int = 200,
    category_id: int,
    body_style: str | None = None,
    year: int | None = None,
    year_range: int = 3,
    market_window_days: int = 90,
) -> dict[str, Any]:
    top_n = max(1, min(int(limit), 300))
    conditions = [
        "v.is_deleted = 0",
        "v.price IS NOT NULL",
        "v.price > 0",
        "v.category_id = ?",
        "v.status IN ('Available', 'Sold', 'Reserved')",
    ]
    params: list[Any] = [category_id]

    if body_style:
        conditions.append("v.body_style = ?")
        params.append(body_style)
    if year is not None:
        conditions.append("v.year BETWEEN ? AND ?")
        params.extend([year - year_range, year + year_range])
    if market_window_days > 0:
        conditions.append("COALESCE(CAST(v.posting_date AS date), CAST(v.created_at AS date)) >= DATEADD(DAY, ?, CAST(GETDATE() AS date))")
        params.append(-abs(int(market_window_days)))

    where = " AND ".join(conditions)
    sql = f"""
SELECT TOP {top_n}
    CAST(v.id AS varchar(50)) AS listingId,
    v.id AS vehicleId,
    v.category_id AS categoryId,
    v.subcategory_id AS subcategoryId,
    v.title,
    CAST(v.price AS bigint) AS price,
    v.year,
    v.mileage,
    v.fuel,
    v.transmission,
    v.body_style AS bodyStyle,
    v.origin,
    v.branch_id AS branchId,
    v.status,
    CONVERT(varchar(10), COALESCE(CAST(v.posting_date AS date), CAST(v.created_at AS date)), 23) AS postingDate
FROM Vehicles v
WHERE {where}
ORDER BY COALESCE(v.posting_date, v.created_at) DESC, v.id DESC
"""
    items = sqlserver.query_positional_readonly(sql, params=params)
    return {"items": items, "count": len(items)}


def pricing_get_market_status_summary(*, category_id: int, subcategory_id: int) -> dict[str, Any]:
    sql = """
SELECT v.status, COUNT(*) AS cnt
FROM Vehicles v
WHERE v.is_deleted = 0 AND v.category_id = ? AND v.subcategory_id = ?
GROUP BY v.status
"""
    rows = sqlserver.query_positional_readonly(sql, params=[category_id, subcategory_id])
    return {"items": rows, "count": len(rows)}


def pricing_get_market_recency_summary(*, category_id: int, subcategory_id: int, market_window_days: int = 90) -> dict[str, Any]:
    sql = """
SELECT COUNT(*) AS recentCount
FROM Vehicles v
WHERE
    v.is_deleted = 0
    AND v.category_id = ?
    AND v.subcategory_id = ?
    AND COALESCE(CAST(v.posting_date AS date), CAST(v.created_at AS date)) >= DATEADD(DAY, ?, CAST(GETDATE() AS date))
"""
    rows = sqlserver.query_positional_readonly(sql, params=[category_id, subcategory_id, -abs(int(market_window_days))])
    return rows[0] if rows else {"recentCount": 0}


PRICING_TOOLS: list[dict[str, Any]] = [
    {"name": "pricing_validate_reference_data", "handler": pricing_validate_reference_data},
    {"name": "pricing_get_market_candidates", "handler": pricing_get_market_candidates},
    {"name": "pricing_get_segment_candidates", "handler": pricing_get_segment_candidates},
    {"name": "pricing_get_market_status_summary", "handler": pricing_get_market_status_summary},
    {"name": "pricing_get_market_recency_summary", "handler": pricing_get_market_recency_summary},
]
