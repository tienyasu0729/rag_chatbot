"""
Embedding service singleton.
Hỗ trợ local SentenceTransformer và OpenAI-compatible embeddings API.
"""

import logging
import threading
from typing import Any

import torch

from app.config import get_settings

logger = logging.getLogger(__name__)

_model: Any = None
_model_lock = threading.Lock()
_is_ready = False
_backend: str | None = None


def _resolve_device(device: str | None) -> str:
    """Tự động chọn device phù hợp: cuda nếu khả dụng, ngược lại cpu."""
    if device is not None and device != "auto":
        return device

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_mem / (1024 ** 3)
        logger.info("GPU detected: %s (%.1f GB VRAM)", gpu_name, gpu_mem)
        return "cuda"

    logger.info("No CUDA GPU available, using CPU")
    return "cpu"


def load_model(model_name: str = "BAAI/bge-m3", device: str | None = None):
    """
    Khởi tạo embedding backend. Gọi 1 lần khi app khởi động.
    Thread-safe qua lock.
    device=None -> tự động detect (cuda/cpu) cho local backend.
    """
    global _model, _is_ready, _backend

    with _model_lock:
        if _model is not None:
            return

        settings = get_settings()
        provider = settings.EMBEDDING_PROVIDER.strip().lower() or "local"

        if provider == "openai":
            if not settings.EMBEDDING_API_KEY:
                raise RuntimeError(
                    "EMBEDDING_API_KEY là bắt buộc khi EMBEDDING_PROVIDER=openai"
                )

            from openai import OpenAI

            _model = OpenAI(
                api_key=settings.EMBEDDING_API_KEY,
                base_url=settings.EMBEDDING_BASE_URL or None,
            )
            _backend = provider
            _is_ready = True
            logger.info(
                "Embedding API client initialized (provider=%s, model=%s, base_url=%s)",
                provider,
                model_name,
                settings.EMBEDDING_BASE_URL or "default",
            )
            return

        if provider != "local":
            raise RuntimeError(
                f"Unsupported EMBEDDING_PROVIDER='{settings.EMBEDDING_PROVIDER}'"
            )

        resolved_device = _resolve_device(device)
        logger.info(
            "Loading local embedding model: %s (device: %s)...",
            model_name,
            resolved_device,
        )
        from sentence_transformers import SentenceTransformer

        try:
            _model = SentenceTransformer(model_name, device=resolved_device)
        except (AssertionError, RuntimeError) as exc:
            if resolved_device != "cpu":
                logger.warning(
                    "Failed to load model on '%s' (%s). Falling back to CPU...",
                    resolved_device, exc,
                )
                _model = SentenceTransformer(model_name, device="cpu")
            else:
                raise

        _backend = provider
        _is_ready = True
        logger.info(
            "Local embedding model loaded successfully (device: %s).",
            _model.device,
        )


def is_ready() -> bool:
    """Kiểm tra model đã load xong chưa."""
    return _is_ready


def embed_text(text: str) -> list[float]:
    """
    Embed 1 đoạn text thành dense vector.
    """
    if not _is_ready or _model is None:
        raise RuntimeError("Embedding service chưa sẵn sàng")

    settings = get_settings()
    if _backend == "openai":
        response = _model.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    vector = _model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Embed nhiều text cùng lúc. Dùng cho embedding pipeline.
    """
    if not texts:
        return []

    if not _is_ready or _model is None:
        raise RuntimeError("Embedding service chưa sẵn sàng")

    settings = get_settings()
    if _backend == "openai":
        response = _model.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    vectors = _model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    return [vec.tolist() for vec in vectors]
