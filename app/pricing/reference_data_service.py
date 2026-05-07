"""
Lay du lieu category/subcategory phuc vu dropdown frontend pricing UI.
Khong thuoc pricing engine va khong di qua pricing_* MCP tools.
"""

from __future__ import annotations

from app.db import sqlserver


def get_pricing_reference_options() -> dict:
    categories_sql = """
SELECT
    c.id,
    c.name,
    COUNT(*) AS vehicle_count
FROM Vehicles v
JOIN Categories c ON c.id = v.category_id
WHERE
    v.is_deleted = 0
    AND v.status IN ('Available', 'Sold', 'Reserved')
GROUP BY c.id, c.name
ORDER BY c.name ASC
"""
    subcategories_sql = """
WITH vehicle_scope AS (
    SELECT
        v.id,
        v.subcategory_id,
        v.category_id
    FROM Vehicles v
    WHERE
        v.is_deleted = 0
        AND v.status IN ('Available', 'Sold', 'Reserved')
),
category_votes AS (
    SELECT
        vs.subcategory_id,
        vs.category_id,
        COUNT(*) AS vote_count
    FROM vehicle_scope vs
    GROUP BY vs.subcategory_id, vs.category_id
),
best_category AS (
    SELECT
        cv.subcategory_id,
        cv.category_id,
        cv.vote_count,
        ROW_NUMBER() OVER (
            PARTITION BY cv.subcategory_id
            ORDER BY cv.vote_count DESC, cv.category_id ASC
        ) AS rn
    FROM category_votes cv
),
subcat_counts AS (
    SELECT
        vs.subcategory_id,
        COUNT(*) AS vehicle_count
    FROM vehicle_scope vs
    GROUP BY vs.subcategory_id
)
SELECT
    sc.id,
    sc.name,
    sc.name_normalized,
    sc.status,
    bc.category_id,
    c.name AS category_name,
    scc.vehicle_count
FROM Subcategories sc
JOIN subcat_counts scc ON scc.subcategory_id = sc.id
JOIN best_category bc ON bc.subcategory_id = sc.id AND bc.rn = 1
JOIN Categories c ON c.id = bc.category_id
WHERE sc.status = 'active'
ORDER BY c.name ASC, sc.name ASC
"""
    categories = sqlserver.query_positional_readonly(categories_sql)
    subcategories = sqlserver.query_positional_readonly(subcategories_sql)
    return {
        "categories": categories,
        "subcategories": subcategories,
        "counts": {
            "categories": len(categories),
            "subcategories": len(subcategories),
        },
    }
