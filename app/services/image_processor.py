"""
Xu ly anh cho bai toan dinh gia nhap xe.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from fastapi import UploadFile
from PIL import Image, ImageOps

from app.models.schemas import ImageTag

logger = logging.getLogger(__name__)

MAX_EDGE = 768
GRID_SIZE = 768
GRID_TILE_SIZE = GRID_SIZE // 2
GRID_BUCKETS: tuple[ImageTag, ...] = ("exterior_overview", "interior")
MAX_GRID_IMAGES = 4
MAX_DAMAGE_IMAGES = 4


@dataclass
class VisionImagePayload:
    label: str
    mime_type: str
    data: bytes


@dataclass
class ProcessedImageBundle:
    payload_images: list[VisionImagePayload]
    accepted_count: int
    skipped_count: int
    bucket_counts: dict[str, int]


async def prepare_images_for_assessment(
    images: list[UploadFile],
    image_tags: list[ImageTag],
) -> ProcessedImageBundle:
    if not images:
        raise ValueError("Phai upload it nhat 1 anh")
    if len(images) != len(image_tags):
        raise ValueError("So luong images va image_tags phai khop nhau")

    grouped: dict[str, list[Image.Image]] = {
        "exterior_overview": [],
        "interior": [],
        "detail_damage": [],
    }
    accepted_count = 0
    skipped_count = 0

    for upload, tag in zip(images, image_tags):
        raw = await upload.read()
        if not raw:
            skipped_count += 1
            continue

        try:
            normalized = _normalize_image(raw)
        except Exception:
            skipped_count += 1
            logger.warning("Bo qua anh khong hop le: %s", upload.filename)
            continue

        grouped[tag].append(normalized)
        accepted_count += 1

    payload_images: list[VisionImagePayload] = []

    for bucket in GRID_BUCKETS:
        selected = grouped[bucket][:MAX_GRID_IMAGES]
        if not selected:
            continue
        payload_images.append(
            VisionImagePayload(
                label=f"{bucket}_grid",
                mime_type="image/jpeg",
                data=_render_grid(selected),
            )
        )

    for index, image in enumerate(grouped["detail_damage"][:MAX_DAMAGE_IMAGES], start=1):
        payload_images.append(
            VisionImagePayload(
                label=f"detail_damage_{index}",
                mime_type="image/jpeg",
                data=_image_to_jpeg_bytes(image),
            )
        )

    if not payload_images:
        raise ValueError("Khong co anh hop le de phan tich")

    return ProcessedImageBundle(
        payload_images=payload_images,
        accepted_count=accepted_count,
        skipped_count=skipped_count,
        bucket_counts={key: len(value) for key, value in grouped.items()},
    )


def _normalize_image(raw: bytes) -> Image.Image:
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source)
        image = image.convert("RGB")
        image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
        return image.copy()


def _render_grid(images: list[Image.Image]) -> bytes:
    canvas = Image.new("RGB", (GRID_SIZE, GRID_SIZE), color=(245, 245, 245))

    for idx, image in enumerate(images[:MAX_GRID_IMAGES]):
        tile = ImageOps.contain(image, (GRID_TILE_SIZE, GRID_TILE_SIZE), Image.Resampling.LANCZOS)
        tile_canvas = Image.new("RGB", (GRID_TILE_SIZE, GRID_TILE_SIZE), color=(255, 255, 255))
        offset = (
            (GRID_TILE_SIZE - tile.width) // 2,
            (GRID_TILE_SIZE - tile.height) // 2,
        )
        tile_canvas.paste(tile, offset)
        x = (idx % 2) * GRID_TILE_SIZE
        y = (idx // 2) * GRID_TILE_SIZE
        canvas.paste(tile_canvas, (x, y))

    return _image_to_jpeg_bytes(canvas)


def _image_to_jpeg_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80, optimize=True)
    return buffer.getvalue()
