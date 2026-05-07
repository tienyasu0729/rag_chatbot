from app.pricing.errors import PricingError
from app.pricing.pricing_tools_executor import execute_pricing_tool
from app.pricing.service import build_valuation_id


def test_pricing_executor_rejects_non_pricing_tools():
    try:
        execute_pricing_tool("count_vehicles", {})
    except PricingError as exc:
        assert exc.code == "market_data_unavailable"
    else:
        raise AssertionError("Expected PricingError")


def test_build_valuation_id_prefix():
    assert build_valuation_id().startswith("val_")

