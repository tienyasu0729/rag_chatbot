"""
Registry và executor cho MCP tools.
"""

from __future__ import annotations

from app.mcp.security import (
    InvalidParamsError,
    sanitize_string_params,
    validate_enum_params,
    validate_params_shape,
)
from app.mcp.tools import TOOLS


class UnknownToolError(ValueError):
    """Tool không tồn tại trong whitelist."""


_TOOL_MAP = {tool["name"]: tool for tool in TOOLS}


def get_tool_schemas_for_ai() -> list[dict]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        }
        for tool in TOOLS
    ]


def execute_tool(tool_name: str, params: dict) -> dict:
    tool = _TOOL_MAP.get(tool_name)
    if tool is None:
        raise UnknownToolError(tool_name)

    schema = tool["parameters"]
    validated = validate_params_shape(params or {}, schema)
    sanitized = sanitize_string_params(validated)
    normalized = validate_enum_params(sanitized, schema)
    result = tool["handler"](**normalized)
    return {"tool": tool_name, "params_used": normalized, "result": result}
