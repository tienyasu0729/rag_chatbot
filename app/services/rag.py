"""
RAG flow — embed query + tìm kiếm Qdrant + SQL gate verify.
Hỗ trợ filter theo preferences (giá, nhiên liệu, hộp số).
"""

import logging
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

from app.config import get_settings
from app.db.qdrant import get_qdrant_client, raise_qdrant_unavailable, QdrantUnavailableError
from app.db import sqlserver
from app.services.embedding import embed_text

logger = logging.getLogger(__name__)


def _build_filter(preferences: dict | None) -> Filter:
    """Build Qdrant filter from status + user preferences."""
    must = [
        FieldCondition(key="status", match=MatchValue(value="Available")),
    ]

    if preferences:
        budget_max = preferences.get("ngan_sach_max")
        budget_min = preferences.get("ngan_sach_min")
        if budget_max is not None or budget_min is not None:
            range_params = {}
            if budget_max is not None:
                range_params["lte"] = float(budget_max)
            if budget_min is not None:
                range_params["gte"] = float(budget_min)
            must.append(FieldCondition(key="gia", range=Range(**range_params)))

        fuel = preferences.get("nhien_lieu")
        if fuel:
            must.append(FieldCondition(key="fuel", match=MatchValue(value=fuel)))

        transmission = preferences.get("hop_so")
        if transmission:
            must.append(FieldCondition(key="transmission", match=MatchValue(value=transmission)))

    return Filter(must=must)


def rag_search(
    query: str,
    preferences: dict | None = None,
    top_k: int = 5,
) -> tuple[list[str], list[int]]:
    """
    Embed câu hỏi → tìm kiếm vector trong Qdrant → SQL gate verify.
    Returns: (texts, vehicle_ids) — chỉ xe thực sự còn Available trong DB.
    """
    settings = get_settings()

    try:
        query_vector = embed_text(query)

        try:
            results = get_qdrant_client().search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_vector,
                query_filter=_build_filter(preferences),
                limit=top_k * 2,
                score_threshold=settings.QDRANT_SCORE_THRESHOLD,
            )
        except Exception as exc:
            raise_qdrant_unavailable("search", exc)

        candidate_ids = [
            r.payload["vehicle_id"] for r in results
            if r.payload.get("vehicle_id")
        ]

        if not candidate_ids:
            logger.info("RAG search: query='%s' → 0 candidates", query[:80])
            return [], []

        placeholders = ",".join(["?"] * len(candidate_ids))
        verified = sqlserver.query_positional(
            f"""SELECT id FROM Vehicles
                WHERE id IN ({placeholders})
                  AND status = 'Available'
                  AND is_deleted = 0""",
            params=candidate_ids,
        )
        verified_ids = {r["id"] for r in verified}

        texts = []
        final_ids = []
        for r in results:
            vid = r.payload.get("vehicle_id")
            if vid in verified_ids and r.payload.get("text"):
                texts.append(r.payload["text"])
                final_ids.append(vid)
                if len(texts) >= top_k:
                    break

        logger.info(
            "RAG search: query='%s' → %d Qdrant hits, %d verified (threshold=%.2f, prefs=%s)",
            query[:80], len(results), len(texts), settings.QDRANT_SCORE_THRESHOLD,
            bool(preferences),
        )
        return texts, final_ids

    except QdrantUnavailableError:
        logger.warning("RAG search skipped because Qdrant is unavailable")
        raise
    except Exception:
        logger.exception("RAG search failed")
        return [], []
