from types import SimpleNamespace

from app.services.image_processor import ProcessedImageBundle, VisionImagePayload
from app.services import vision_analysis


def test_analyze_vehicle_condition_returns_default_when_beeknoee_fails(monkeypatch):
    bundle = ProcessedImageBundle(
        payload_images=[VisionImagePayload(label="x", mime_type="image/jpeg", data=b"123")],
        accepted_count=1,
        skipped_count=0,
        bucket_counts={"exterior_overview": 1, "interior": 0, "detail_damage": 0},
    )

    monkeypatch.setattr(
        vision_analysis,
        "get_settings",
        lambda: SimpleNamespace(
            VISION_API_KEY="sk-bee-fake",
            VISION_BASE_URL="https://platform.beeknoee.com/api/v1",
            VISION_MODEL="fake-vision-model",
        ),
    )

    class BrokenOpenAI:
        def __init__(self, api_key: str, base_url: str):
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(vision_analysis, "OpenAI", BrokenOpenAI)

    result = vision_analysis.analyze_vehicle_condition(bundle)

    assert result["condition_score"] == 60
    assert result["damage_percentage"]["scratch"] == "unknown"
    assert "Khong phan tich duoc anh tu Beeknoee" in result["risk_flags"][0]
