"""
Guardrail cho market reference, fair price va deal suggestion.
"""

from __future__ import annotations

from app.pricing.errors import PricingError


def apply_guardrails(prices: dict, market_stats: dict, *, fallback_level: int, variant_confidence: float, result_type: str | None = None) -> None:
    market = prices["marketReferencePrice"]
    fair = prices["fairPrice"]
    purchase = prices["purchasePrice"]
    deal = prices["dealSuggestion"]
    p25 = market_stats.get("p25Price")
    p75 = market_stats.get("p75Price")

    market_median = market.get("median")
    fair_price = fair.get("suggestedPrice")
    purchase_price = purchase.get("suggestedPrice")

    if market_median is not None and p25 is not None and market_median < int(p25 * 0.9):
        raise PricingError("pricing_guardrail_failed", "Market reference thap hon guardrail cho phep", status_code=422)
    if market_median is not None and p75 is not None and market_median > int(p75 * 1.1):
        raise PricingError("pricing_guardrail_failed", "Market reference cao hon guardrail cho phep", status_code=422)
    if market_median is not None and fair_price is not None and fair_price > market_median:
        raise PricingError("pricing_guardrail_failed", "Fair price khong duoc cao hon market reference", status_code=422)
    if fair_price is not None and purchase_price is not None and purchase_price >= fair_price:
        raise PricingError("pricing_guardrail_failed", "Purchase price phai thap hon fair price", status_code=422)
    if purchase_price is not None and deal.get("recommendedOfferPrice") is not None and deal["recommendedOfferPrice"] > deal.get("maxAcceptablePurchasePrice"):
        raise PricingError("pricing_guardrail_failed", "Negotiation range khong hop le", status_code=422)
    if result_type in {"rough_segment_estimate", "insufficient_market_data"} and purchase_price is not None:
        raise PricingError("pricing_guardrail_failed", "Fallback level cao khong duoc tra purchasePrice chac chan", status_code=422)
