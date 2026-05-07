"""
Qdrant client singleton + khởi tạo collection.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None
_qdrant_status = {
    "available": False,
    "last_error": None,
}


class QdrantUnavailableError(RuntimeError):
    """Qdrant không reachable hoặc thao tác remote thất bại."""


def _set_qdrant_status(available: bool, error: str | None = None) -> None:
    _qdrant_status["available"] = available
    _qdrant_status["last_error"] = error


def get_qdrant_status() -> dict[str, Any]:
    return {
        "available": bool(_qdrant_status["available"]),
        "last_error": _qdrant_status["last_error"],
    }


def is_qdrant_available() -> bool:
    return bool(_qdrant_status["available"])


def raise_qdrant_unavailable(action: str, exc: Exception) -> None:
    message = f"Qdrant {action} failed: {exc}"
    _set_qdrant_status(False, str(exc))
    raise QdrantUnavailableError(message) from exc


def resolve_embedding_dimension() -> int:
    """Suy ra vector dimension từ embedding provider/model hiện tại."""
    settings = get_settings()
    provider = settings.EMBEDDING_PROVIDER.strip().lower() or "local"
    model_name = settings.EMBEDDING_MODEL.strip()

    if provider == "local":
        return 1024

    if provider != "openai":
        raise RuntimeError(
            f"Unsupported EMBEDDING_PROVIDER='{settings.EMBEDDING_PROVIDER}'"
        )

    if model_name == "text-embedding-3-small":
        return 1536
    if model_name == "text-embedding-3-large":
        return 3072

    raise RuntimeError(
        f"Unsupported OpenAI embedding model '{model_name}'. "
        "Hãy bổ sung mapping dimension trước khi khởi tạo Qdrant collection."
    )


def _extract_vector_size(vectors_config: Any) -> int | None:
    """Lấy vector size từ cấu hình collection hiện có."""
    if vectors_config is None:
        return None

    if isinstance(vectors_config, dict):
        if "size" in vectors_config:
            return vectors_config["size"]
        for value in vectors_config.values():
            size = _extract_vector_size(value)
            if size is not None:
                return size
        return None

    size = getattr(vectors_config, "size", None)
    if size is not None:
        return size

    for attr in ("model_dump", "dict"):
        dump_fn = getattr(vectors_config, attr, None)
        if callable(dump_fn):
            dumped = dump_fn()
            size = _extract_vector_size(dumped)
            if size is not None:
                return size

    return None


def get_qdrant_client() -> QdrantClient:
    """Singleton Qdrant client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        logger.info(
            "Qdrant client connected: %s:%s",
            settings.QDRANT_HOST,
            settings.QDRANT_PORT,
        )
    return _client


def init_collection():
    """
    Khởi tạo collection nếu chưa tồn tại.
    Vector size phụ thuộc embedding model hiện tại, distance = COSINE.
    """
    settings = get_settings()
    client = get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION
    expected_size = resolve_embedding_dimension()

    try:
        collections = [c.name for c in client.get_collections().collections]
    except Exception as exc:
        raise_qdrant_unavailable("get_collections", exc)

    if collection_name not in collections:
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=expected_size, distance=Distance.COSINE),
            )
        except Exception as exc:
            raise_qdrant_unavailable("create_collection", exc)
        logger.info(
            "Created Qdrant collection: %s (vector size: %d)",
            collection_name,
            expected_size,
        )
        _set_qdrant_status(True, None)
        return

    try:
        collection_info = client.get_collection(collection_name)
    except Exception as exc:
        raise_qdrant_unavailable("get_collection", exc)

    vectors_config = getattr(
        getattr(getattr(collection_info, "config", None), "params", None),
        "vectors",
        None,
    )
    actual_size = _extract_vector_size(vectors_config)

    if actual_size is None:
        logger.warning(
            "Could not determine vector size for existing Qdrant collection '%s'",
            collection_name,
        )
        _set_qdrant_status(True, None)
        return

    if actual_size != expected_size:
        raise RuntimeError(
            "Qdrant collection "
            f"'{collection_name}' đang có vector size={actual_size}, "
            f"nhưng embedding model '{settings.EMBEDDING_MODEL}' cần size={expected_size}. "
            "Hãy đổi QDRANT_COLLECTION hoặc recreate collection rồi sync lại."
        )

    logger.info(
        "Qdrant collection '%s' already exists with matching vector size=%d",
        collection_name,
        actual_size,
    )
    _set_qdrant_status(True, None)
