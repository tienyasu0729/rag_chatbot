"""
Dispatcher MCP -> SQL agent fallback.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Callable

from app.mcp.registry import execute_tool, get_tool_schemas_for_ai
from app.mcp.security import InvalidParamsError
from app.services.llm import json_completion
from app.services.mcp_logging import log_mcp_query
from app.services.sql_agent import generate_and_execute_sql

logger = logging.getLogger(__name__)

_SELECT_TOOL_SYSTEM_PROMPT = """Bạn là bộ định tuyến tool cho chatbot xe hơi.
Nhiệm vụ: chỉ chọn đúng 1 tool MCP nếu câu hỏi khớp rõ ràng với tool schema.
Nếu không khớp rõ ràng hoặc câu hỏi quá phức tạp, trả {"tool": null, "params": {}}.
Chỉ trả JSON object hợp lệ. Không thêm markdown, không giải thích.
"""


def select_tool(query: str, history: list[dict]) -> dict | None:
    tool_schemas = get_tool_schemas_for_ai()
    history_text = "\n".join(
        f"- {item.get('role', 'user')}: {item.get('content', '')}"
        for item in history[-6:]
    ) or "(Không có lịch sử)"
    user_prompt = (
        f"Các tool hiện có:\n{json.dumps(tool_schemas, ensure_ascii=False, indent=2)}\n\n"
        f"Lịch sử gần nhất:\n{history_text}\n\n"
        f"Câu hỏi hiện tại: {query}\n\n"
        'Trả JSON dạng {"tool": "tool_name", "params": {...}} hoặc {"tool": null, "params": {}}.'
    )

    try:
        payload = json_completion(
            messages=[
                {"role": "system", "content": _SELECT_TOOL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            schema_hint='{"tool": "string|null", "params": "object"}',
            temperature=0.0,
            max_tokens=600,
        )
    except Exception:
        logger.warning("MCP selector failed", exc_info=True)
        return None

    if not isinstance(payload, dict):
        return None
    tool_name = payload.get("tool")
    params = payload.get("params") or {}
    if tool_name is None:
        return None
    if not isinstance(tool_name, str) or not isinstance(params, dict):
        return None
    available_names = {tool["name"] for tool in tool_schemas}
    if tool_name not in available_names:
        return None
    return {"tool": tool_name, "params": params}


def dispatch(
    query: str,
    history: list[dict],
    preferences: dict | None = None,
    db_fallback_fn: Callable[[str, dict | None], list[dict] | None] | None = None,
    session_id: int | None = None,
) -> dict:
    tool_call = select_tool(query, history)

    if tool_call is not None:
        started = time.perf_counter()
        try:
            tool_response = execute_tool(tool_call["tool"], tool_call["params"])
            results = tool_response["result"]
            latency_ms = int((time.perf_counter() - started) * 1000)
            result_count = len(results) if isinstance(results, list) else 1
            log_mcp_query(
                session_id=session_id,
                query_text=query,
                source="mcp",
                tool_selected=tool_call["tool"],
                params=tool_response["params_used"],
                success=True,
                result_count=result_count,
                latency_ms=latency_ms,
            )
            return {
                "success": True,
                "sql": None,
                "results": results,
                "error": None,
                "source": "mcp",
                "tool": tool_call["tool"],
            }
        except InvalidParamsError as exc:
            logger.warning("MCP tool params invalid, fallback to sql_agent: %s", exc)
        except Exception:
            logger.warning("MCP tool execution failed, fallback to sql_agent", exc_info=True)

    started = time.perf_counter()
    sql_result = generate_and_execute_sql(query)
    latency_ms = int((time.perf_counter() - started) * 1000)

    if sql_result.get("success"):
        rows = sql_result.get("results") or []
        log_mcp_query(
            session_id=session_id,
            query_text=query,
            source="sql_agent",
            tool_selected=None,
            params=None,
            success=True,
            result_count=len(rows),
            latency_ms=latency_ms,
        )
        sql_result["source"] = "sql_agent"
        return sql_result

    if db_fallback_fn is not None:
        started = time.perf_counter()
        fallback_rows = db_fallback_fn(query, preferences)
        fallback_latency = int((time.perf_counter() - started) * 1000)
        if fallback_rows:
            log_mcp_query(
                session_id=session_id,
                query_text=query,
                source="db_fallback",
                tool_selected=None,
                params=None,
                success=True,
                result_count=len(fallback_rows),
                latency_ms=fallback_latency,
            )
            return {
                "success": True,
                "sql": None,
                "results": fallback_rows,
                "error": None,
                "source": "db_fallback",
            }

    log_mcp_query(
        session_id=session_id,
        query_text=query,
        source="sql_agent",
        tool_selected=None,
        params=None,
        success=False,
        result_count=0,
        latency_ms=latency_ms,
    )
    sql_result["source"] = "sql_agent"
    return sql_result
