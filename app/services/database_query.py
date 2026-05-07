"""
DatabaseQueryService — truy vấn tổng hợp trực tiếp SQL Server.
Bypass vector search hoàn toàn, trả về con số chính xác 100%.
"""

import re
import logging
from datetime import datetime, timezone

from app.db import sqlserver

logger = logging.getLogger(__name__)

_SAFE_KEYWORD = re.compile(r"^[\w\s\-]+$", re.UNICODE)

_BASE_WHERE = "v.status = 'Available' AND v.is_deleted = 0"

_FROM_CLAUSE = """
    FROM Vehicles v
    JOIN Categories    c  ON v.category_id    = c.id
    JOIN Subcategories sc ON v.subcategory_id = sc.id
    LEFT JOIN Branches b  ON v.branch_id      = b.id
"""


def count_vehicles(
    *,
    title_keyword: str | None = None,
    fuel: str | None = None,
    transmission: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    category: str | None = None,
    subcategory: str | None = None,
) -> int:
    """Đếm xe Available khớp bộ lọc. Trả về COUNT chính xác từ SQL Server."""
    conditions = [_BASE_WHERE]
    params: list = []

    if title_keyword and _SAFE_KEYWORD.match(title_keyword):
        conditions.append("v.title LIKE ?")
        params.append(f"%{title_keyword}%")

    if fuel:
        conditions.append("v.fuel = ?")
        params.append(fuel)

    if transmission:
        conditions.append("v.transmission = ?")
        params.append(transmission)

    if budget_min is not None:
        conditions.append("v.price >= ?")
        params.append(float(budget_min))

    if budget_max is not None:
        conditions.append("v.price <= ?")
        params.append(float(budget_max))

    if category and _SAFE_KEYWORD.match(category):
        conditions.append("c.name LIKE ?")
        params.append(f"%{category}%")

    if subcategory and _SAFE_KEYWORD.match(subcategory):
        conditions.append("sc.name LIKE ?")
        params.append(f"%{subcategory}%")

    where = " AND ".join(conditions)
    sql = f"SELECT COUNT(*) AS cnt {_FROM_CLAUSE} WHERE {where}"

    row = sqlserver.query_positional(sql, params=params or None)
    return row[0]["cnt"] if row else 0


def get_inventory_snapshot() -> dict:
    """
    Thống kê tổng quan kho xe real-time.
    Returns dict: total, by_category [{name, count}], timestamp.
    """
    total_row = sqlserver.query_positional(
        f"SELECT COUNT(*) AS cnt FROM Vehicles v WHERE {_BASE_WHERE}"
    )
    total = total_row[0]["cnt"] if total_row else 0

    by_category = sqlserver.query_positional(f"""
        SELECT c.name, COUNT(*) AS cnt
        {_FROM_CLAUSE}
        WHERE {_BASE_WHERE}
        GROUP BY c.name
        ORDER BY cnt DESC
    """)

    return {
        "total": total,
        "by_category": [{"name": r["name"], "count": r["cnt"]} for r in by_category],
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def format_stats_header(snapshot: dict) -> str:
    """Render snapshot thành text block để inject vào prompt."""
    lines = [
        "=== THỐNG KÊ THẬT TỪ DATABASE ===",
        f"Tổng xe đang bán: {snapshot['total']} xe",
    ]
    for cat in snapshot["by_category"]:
        lines.append(f"- {cat['name']}: {cat['count']} xe")
    lines.append(f"Cập nhật lúc: {snapshot['timestamp']}")
    lines.append("=" * 35)
    return "\n".join(lines)


def format_filtered_count(count: int, label: str) -> str:
    """Render COUNT có điều kiện thành dòng ngắn gọn cho context."""
    return f"[THỐNG KÊ THẬT TỪ DATABASE] Tổng số {label}: {count} xe"
