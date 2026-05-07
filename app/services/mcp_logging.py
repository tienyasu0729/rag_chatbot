"""
Logging và stats cho MCP dispatcher.
"""

from __future__ import annotations

import json
import logging

from app.db import sqlserver

logger = logging.getLogger(__name__)


def log_mcp_query(
    *,
    session_id: int | None,
    query_text: str,
    source: str,
    tool_selected: str | None,
    params: dict | None,
    success: bool,
    result_count: int,
    latency_ms: int,
) -> None:
    try:
        sqlserver.execute(
            """
            INSERT INTO MCP_Query_Log (
                session_id, query_text, source, tool_selected, params_json,
                success, result_count, latency_ms, created_at
            )
            VALUES (
                @session_id, @query_text, @source, @tool_selected, @params_json,
                @success, @result_count, @latency_ms, SYSUTCDATETIME()
            )
            """,
            params={
                "session_id": session_id,
                "query_text": query_text,
                "source": source,
                "tool_selected": tool_selected,
                "params_json": json.dumps(params or {}, ensure_ascii=False),
                "success": 1 if success else 0,
                "result_count": result_count,
                "latency_ms": latency_ms,
            },
        )
    except Exception:
        logger.warning("Không thể ghi MCP_Query_Log", exc_info=True)


def get_mcp_stats(days: int = 7) -> dict:
    try:
        summary = sqlserver.query(
            """
            SELECT source, COUNT(*) AS total, AVG(CAST(latency_ms AS FLOAT)) AS avg_latency_ms
            FROM MCP_Query_Log
            WHERE created_at >= DATEADD(DAY, -@days, SYSUTCDATETIME())
            GROUP BY source
            ORDER BY total DESC
            """,
            params={"days": days},
        )
        tool_success = sqlserver.query(
            """
            SELECT
                tool_selected,
                COUNT(*) AS total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_count,
                AVG(CAST(latency_ms AS FLOAT)) AS avg_latency_ms
            FROM MCP_Query_Log
            WHERE created_at >= DATEADD(DAY, -@days, SYSUTCDATETIME())
              AND tool_selected IS NOT NULL
            GROUP BY tool_selected
            ORDER BY total DESC, tool_selected ASC
            """,
            params={"days": days},
        )
        sql_agent_queries = sqlserver.query(
            """
            SELECT TOP 10 query_text, COUNT(*) AS total
            FROM MCP_Query_Log
            WHERE created_at >= DATEADD(DAY, -@days, SYSUTCDATETIME())
              AND source = 'sql_agent'
            GROUP BY query_text
            ORDER BY total DESC, query_text ASC
            """,
            params={"days": days},
        )
    except Exception:
        logger.warning("Không thể đọc MCP_Query_Log, trả stats rỗng", exc_info=True)
        return {
            "window_days": days,
            "total_requests": 0,
            "source_breakdown": [],
            "tool_success": [],
            "top_sql_agent_queries": [],
        }

    total_requests = sum(row["total"] for row in summary)
    source_breakdown = []
    for row in summary:
        total = row["total"]
        ratio = (total / total_requests) if total_requests else 0
        source_breakdown.append(
            {
                "source": row["source"],
                "total": total,
                "ratio": ratio,
                "avg_latency_ms": row["avg_latency_ms"],
            }
        )

    tool_rows = []
    for row in tool_success:
        total = row["total"]
        success_count = row["success_count"] or 0
        rate = (success_count / total) if total else 0
        tool_rows.append(
            {
                "tool": row["tool_selected"],
                "total": total,
                "success_rate": rate,
                "avg_latency_ms": row["avg_latency_ms"],
            }
        )

    return {
        "window_days": days,
        "total_requests": total_requests,
        "source_breakdown": source_breakdown,
        "tool_success": tool_rows,
        "top_sql_agent_queries": [
            {"query_text": row["query_text"], "total": row["total"]}
            for row in sql_agent_queries
        ],
    }
