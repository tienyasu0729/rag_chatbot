"""
Executor rieng cho pricing_* MCP tools.
"""

from __future__ import annotations

from app.mcp.pricing_tools import PRICING_TOOLS
from app.pricing.errors import PricingError

_TOOL_MAP = {tool["name"]: tool for tool in PRICING_TOOLS}


def execute_pricing_tool(tool_name: str, params: dict) -> dict:
    if not tool_name.startswith("pricing_"):
        raise PricingError("market_data_unavailable", "Pricing executor chi chap nhan pricing_* tools", status_code=500)
    tool = _TOOL_MAP.get(tool_name)
    if tool is None:
        raise PricingError("market_data_unavailable", f"Khong tim thay tool {tool_name}", status_code=500)
    return tool["handler"](**(params or {}))

