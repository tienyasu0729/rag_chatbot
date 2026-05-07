import io

import pytest
from fastapi import UploadFile
from PIL import Image

from app.services.image_processor import prepare_images_for_assessment


def _make_upload(name: str, color: tuple[int, int, int]) -> UploadFile:
    image = Image.new("RGB", (1200, 800), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return UploadFile(filename=name, file=buffer)


@pytest.mark.asyncio
async def test_prepare_images_limits_payload_and_keeps_damage_separate():
    images = [
        _make_upload("ext1.png", (255, 0, 0)),
        _make_upload("ext2.png", (200, 0, 0)),
        _make_upload("ext3.png", (150, 0, 0)),
        _make_upload("ext4.png", (100, 0, 0)),
        _make_upload("ext5.png", (50, 0, 0)),
        _make_upload("int1.png", (0, 255, 0)),
        _make_upload("d1.png", (0, 0, 255)),
        _make_upload("d2.png", (0, 0, 200)),
        _make_upload("d3.png", (0, 0, 150)),
        _make_upload("d4.png", (0, 0, 100)),
        _make_upload("d5.png", (0, 0, 50)),
    ]
    tags = [
        "exterior_overview",
        "exterior_overview",
        "exterior_overview",
        "exterior_overview",
        "exterior_overview",
        "interior",
        "detail_damage",
        "detail_damage",
        "detail_damage",
        "detail_damage",
        "detail_damage",
    ]

    bundle = await prepare_images_for_assessment(images, tags)

    labels = [item.label for item in bundle.payload_images]
    assert labels == [
        "exterior_overview_grid",
        "interior_grid",
        "detail_damage_1",
        "detail_damage_2",
        "detail_damage_3",
        "detail_damage_4",
    ]
    assert bundle.accepted_count == 11
    assert bundle.bucket_counts["exterior_overview"] == 5
    assert bundle.bucket_counts["detail_damage"] == 5


@pytest.mark.asyncio
async def test_prepare_images_rejects_mismatched_tags():
    with pytest.raises(ValueError):
        await prepare_images_for_assessment(
            [_make_upload("one.png", (1, 2, 3))],
            [],
        )
