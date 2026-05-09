"""
Embedding service singleton.
Dùng OpenAI-compatible embeddings API (EMBEDDING_PROVIDER=openai).
"""

import logging
import threading
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

_model: Any = None
_model_lock = threading.Lock()
_is_ready = False


def load_model(model_name: str = "", device: str | None = None):
    """
    Khởi tạo OpenAI-compatible embedding client.
    Gọi 1 lần khi app khởi động. Thread-safe qua lock.
    """
    global _model, _is_ready

    with _model_lock:
        if _model is not None:
            return

        settings = get_settings()
        provider = settings.EMBEDDING_PROVIDER.strip().lower()

        if provider != "openai":
            raise RuntimeError(
                f"EMBEDDING_PROVIDER='{settings.EMBEDDING_PROVIDER}' không được hỗ trợ. "
                "Chỉ hỗ trợ provider='openai'."
            )

        if not settings.EMBEDDING_API_KEY:
            raise RuntimeError("EMBEDDING_API_KEY là bắt buộc khi EMBEDDING_PROVIDER=openai")

        from openai import OpenAI

        _model = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL or None,
        )
        _is_ready = True
        logger.info(
            "Embedding API client initialized (provider=openai, model=%s, base_url=%s)",
            settings.EMBEDDING_MODEL,
            settings.EMBEDDING_BASE_URL or "default",
        )


def is_ready() -> bool:
    """Kiểm tra embedding client đã sẵn sàng chưa."""
    return _is_ready


def embed_text(text: str) -> list[float]:
    """Embed 1 đoạn text thành dense vector."""
    if not _is_ready or _model is None:
        raise RuntimeError("Embedding service chưa sẵn sàng")

    settings = get_settings()
    response = _model.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def embed_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embed nhiều text cùng lúc. Dùng cho embedding pipeline."""
    if not texts:
        return []

    if not _is_ready or _model is None:
        raise RuntimeError("Embedding service chưa sẵn sàng")

    settings = get_settings()
    response = _model.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
