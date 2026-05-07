"""
MongoDB repository cho pricing logs.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.pricing.errors import PricingError

_client = None


def _get_collection():
    global _client
    settings = get_settings()
    if not settings.PRICING_MONGO_URI.strip():
        raise PricingError("mongodb_persistence_failed", "Chua cau hinh PRICING_MONGO_URI", status_code=500)
    if _client is None:
        from pymongo import MongoClient

        _client = MongoClient(settings.PRICING_MONGO_URI.strip(), serverSelectionTimeoutMS=5000)
    db = _client[settings.PRICING_MONGO_DB.strip()]
    return db[settings.PRICING_MONGO_COLLECTION.strip()]


def save_valuation(document: dict[str, Any]) -> None:
    try:
        collection = _get_collection()
        collection.insert_one(document)
    except PricingError:
        raise
    except Exception as exc:
        raise PricingError("mongodb_persistence_failed", "Khong luu duoc valuation vao MongoDB", status_code=500) from exc

