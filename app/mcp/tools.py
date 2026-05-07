"""
Khai báo MCP tools và handlers.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.db import sqlserver
from app.services.database_query import (
    _BASE_WHERE,
    _FROM_CLAUSE,
    count_vehicles,
    get_inventory_snapshot,
)

DEFAULT_PAGE_SIZE = 10
DEFAULT_PRICE_BUCKETS = [
    {"label": "Dưới 300 triệu", "min": None, "max": 300_000_000},
    {"label": "300-500 triệu", "min": 300_000_000, "max": 500_000_000},
    {"label": "500 triệu - 1 tỷ", "min": 500_000_000, "max": 1_000_000_000},
    {"label": "Trên 1 tỷ", "min": 1_000_000_000, "max": None},
]
KNOWN_BRANDS = [
    "Toyota", "Hyundai", "Kia", "Ford", "Mazda", "Honda", "Mitsubishi", "Suzuki",
    "Mercedes", "BMW", "Audi", "Lexus", "VinFast", "Peugeot", "Isuzu", "Nissan",
    "Chevrolet", "Volkswagen", "Volvo", "Land Rover", "Porsche", "MG", "Subaru",
]


def _build_conditions(
    *,
    brand: str | None = None,
    model_keyword: str | None = None,
    fuel_type: str | None = None,
    transmission: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    category: str | None = None,
) -> tuple[list[str], list]:
    conditions = [_BASE_WHERE]
    params: list = []

    if brand:
        conditions.append("v.title LIKE ?")
        params.append(f"%{brand}%")
    if model_keyword:
        conditions.append("v.title LIKE ?")
        params.append(f"%{model_keyword}%")
    if fuel_type:
        conditions.append("LOWER(v.fuel) = ?")
        params.append(fuel_type.lower())
    if transmission:
        conditions.append("LOWER(v.transmission) = ?")
        params.append(transmission.lower())
    if price_min is not None:
        conditions.append("v.price >= ?")
        params.append(float(price_min))
    if price_max is not None:
        conditions.append("v.price <= ?")
        params.append(float(price_max))
    if category:
        conditions.append("c.name LIKE ?")
        params.append(f"%{category}%")

    return conditions, params


def _build_where_clause(**filters) -> tuple[str, list]:
    conditions, params = _build_conditions(**filters)
    return " AND ".join(conditions), params


def _extract_brand_case_expression() -> str:
    clauses = [f"WHEN v.title LIKE '{brand} %' THEN '{brand}'" for brand in KNOWN_BRANDS]
    clauses += [f"WHEN v.title = '{brand}' THEN '{brand}'" for brand in KNOWN_BRANDS]
    return (
        "CASE "
        + " ".join(clauses)
        + " ELSE LEFT(v.title, CASE WHEN CHARINDEX(' ', v.title + ' ') > 0 "
          "THEN CHARINDEX(' ', v.title + ' ') - 1 ELSE LEN(v.title) END) END"
    )


def handle_count_vehicles(**params) -> dict:
    count = count_vehicles(
        title_keyword=params.get("brand"),
        fuel=params.get("fuel_type"),
        transmission=params.get("transmission"),
        budget_min=params.get("price_min"),
        budget_max=params.get("price_max"),
        category=params.get("category"),
    )
    label_parts = ["xe đang bán"]
    if params.get("brand"):
        label_parts.append(f"hãng {params['brand']}")
    return {"count": count, "label": ", ".join(label_parts)}


def handle_get_price_stats(**params) -> dict:
    where, values = _build_where_clause(
        brand=params.get("brand"),
        fuel_type=params.get("fuel_type"),
        category=params.get("category"),
    )
    rows = sqlserver.query_positional_readonly(
        f"""
        SELECT
            MIN(v.price) AS min_price,
            MAX(v.price) AS max_price,
            AVG(CAST(v.price AS FLOAT)) AS avg_price
        {_FROM_CLAUSE}
        WHERE {where}
        """,
        params=values or None,
    )
    row = rows[0] if rows else {"min_price": None, "max_price": None, "avg_price": None}
    stat_type = params["stat_type"]
    if stat_type == "min":
        return {"min_price": row["min_price"]}
    if stat_type == "max":
        return {"max_price": row["max_price"]}
    if stat_type == "avg":
        return {"avg_price": row["avg_price"]}
    return row


def handle_check_availability(**params) -> dict:
    count = count_vehicles(
        title_keyword=params.get("brand") or params.get("model_keyword"),
        fuel=params.get("fuel_type"),
        transmission=params.get("transmission"),
    )
    criteria_parts = [
        part for part in [
            params.get("brand"),
            params.get("model_keyword"),
            params.get("fuel_type"),
            params.get("transmission"),
        ] if part
    ]
    criteria = ", ".join(criteria_parts) if criteria_parts else "toàn bộ xe"
    return {"available": count > 0, "count": count, "criteria": criteria}


def handle_list_vehicles_paginated(**params) -> dict:
    page = max(params.get("page", 1), 1)
    offset = (page - 1) * DEFAULT_PAGE_SIZE
    sort_map = {
        "newest": "v.created_at DESC, v.id DESC",
        "price_asc": "v.price ASC, v.id DESC",
        "price_desc": "v.price DESC, v.id DESC",
    }
    where, values = _build_where_clause(
        brand=params.get("brand"),
        fuel_type=params.get("fuel_type"),
        transmission=params.get("transmission"),
        price_max=params.get("price_max"),
    )
    sql = f"""
        SELECT
            v.id,
            v.title,
            v.price,
            v.year,
            v.fuel,
            v.transmission,
            c.name AS category,
            sc.name AS subcategory,
            b.name AS branch
        {_FROM_CLAUSE}
        WHERE {where}
        ORDER BY {sort_map[params.get("sort_by", "newest")]}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    rows = sqlserver.query_positional_readonly(sql, params=(values + [offset, DEFAULT_PAGE_SIZE + 1]))
    has_more = len(rows) > DEFAULT_PAGE_SIZE
    return {
        "items": rows[:DEFAULT_PAGE_SIZE],
        "page": page,
        "page_size": DEFAULT_PAGE_SIZE,
        "has_more": has_more,
    }


def handle_get_brand_breakdown(**params) -> list[dict]:
    brand_expr = _extract_brand_case_expression()
    where, values = _build_where_clause(
        fuel_type=params.get("fuel_type"),
        transmission=params.get("transmission"),
    )
    rows = sqlserver.query_positional_readonly(
        f"""
        SELECT
            {brand_expr} AS brand,
            COUNT(*) AS count,
            AVG(CAST(v.price AS FLOAT)) AS avg_price
        {_FROM_CLAUSE}
        WHERE {where}
        GROUP BY {brand_expr}
        HAVING COUNT(*) >= ?
        ORDER BY count DESC, brand ASC
        """,
        params=(values + [params.get("min_count", 1)]),
    )
    return [{"brand": row["brand"], "count": row["count"], "avg_price": row["avg_price"]} for row in rows]


def handle_get_inventory_overview(**params) -> dict:
    snapshot = get_inventory_snapshot()
    by_fuel = sqlserver.query_positional_readonly(
        f"""
        SELECT v.fuel AS name, COUNT(*) AS cnt
        FROM Vehicles v
        WHERE {_BASE_WHERE}
        GROUP BY v.fuel
        ORDER BY cnt DESC
        """
    )
    by_transmission = sqlserver.query_positional_readonly(
        f"""
        SELECT v.transmission AS name, COUNT(*) AS cnt
        FROM Vehicles v
        WHERE {_BASE_WHERE}
        GROUP BY v.transmission
        ORDER BY cnt DESC
        """
    )
    return {
        "total": snapshot["total"],
        "by_category": snapshot["by_category"],
        "by_fuel": [{"name": row["name"], "count": row["cnt"]} for row in by_fuel],
        "by_transmission": [{"name": row["name"], "count": row["cnt"]} for row in by_transmission],
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def handle_get_price_range_distribution(**params) -> list[dict]:
    buckets = params.get("buckets") or DEFAULT_PRICE_BUCKETS
    rows = []
    for bucket in buckets:
        conditions, values = _build_conditions(fuel_type=params.get("fuel_type"))
        if bucket.get("min") is not None:
            conditions.append("v.price >= ?")
            values.append(float(bucket["min"]))
        if bucket.get("max") is not None:
            conditions.append("v.price < ?")
            values.append(float(bucket["max"]))
        sql = f"SELECT COUNT(*) AS cnt FROM Vehicles v WHERE {' AND '.join(conditions)}"
        result = sqlserver.query_positional_readonly(sql, params=values or None)
        count = result[0]["cnt"] if result else 0
        rows.append({"range_label": bucket["label"], "count": count})
    return rows


TOOLS: list[dict] = [
    {
        "name": "count_vehicles",
        "description": "Đếm số lượng xe đang bán theo hãng, nhiên liệu, hộp số, khoảng giá hoặc danh mục.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "brand": {"type": "string"},
                "fuel_type": {"type": "string", "dynamic_enum": "fuel_type"},
                "transmission": {"type": "string", "dynamic_enum": "transmission"},
                "price_min": {"type": "number"},
                "price_max": {"type": "number"},
                "category": {"type": "string"},
            },
        },
        "handler": handle_count_vehicles,
    },
    {
        "name": "get_price_stats",
        "description": "Lấy thống kê giá xe đang bán: thấp nhất, cao nhất, trung bình.",
        "parameters": {
            "type": "object",
            "required": ["stat_type"],
            "additionalProperties": False,
            "properties": {
                "stat_type": {"type": "string", "enum": ["min", "max", "avg", "all"]},
                "brand": {"type": "string"},
                "fuel_type": {"type": "string", "dynamic_enum": "fuel_type"},
                "category": {"type": "string"},
            },
        },
        "handler": handle_get_price_stats,
    },
    {
        "name": "check_availability",
        "description": "Kiểm tra xe còn hàng không theo hãng, model keyword, nhiên liệu, hộp số.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "brand": {"type": "string"},
                "model_keyword": {"type": "string"},
                "fuel_type": {"type": "string", "dynamic_enum": "fuel_type"},
                "transmission": {"type": "string", "dynamic_enum": "transmission"},
            },
        },
        "handler": handle_check_availability,
    },
    {
        "name": "list_vehicles_paginated",
        "description": "Liệt kê danh sách xe với phân trang và sắp xếp an toàn.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "brand": {"type": "string"},
                "fuel_type": {"type": "string", "dynamic_enum": "fuel_type"},
                "transmission": {"type": "string", "dynamic_enum": "transmission"},
                "price_max": {"type": "number"},
                "sort_by": {"type": "string", "enum": ["price_asc", "price_desc", "newest"]},
                "page": {"type": "integer"},
            },
        },
        "handler": handle_list_vehicles_paginated,
    },
    {
        "name": "get_brand_breakdown",
        "description": "Thống kê số lượng xe theo từng hãng cùng giá trung bình.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "fuel_type": {"type": "string", "dynamic_enum": "fuel_type"},
                "transmission": {"type": "string", "dynamic_enum": "transmission"},
                "min_count": {"type": "integer"},
            },
        },
        "handler": handle_get_brand_breakdown,
    },
    {
        "name": "get_inventory_overview",
        "description": "Lấy tổng quan kho xe: tổng số, theo danh mục, nhiên liệu, hộp số.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
        "handler": handle_get_inventory_overview,
    },
    {
        "name": "get_price_range_distribution",
        "description": "Thống kê số lượng xe theo các khoảng giá.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "fuel_type": {"type": "string", "dynamic_enum": "fuel_type"},
                "buckets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        },
                    },
                },
            },
        },
        "handler": handle_get_price_range_distribution,
    },
]
