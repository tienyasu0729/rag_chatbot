"""
Pydantic schemas cho API request/response.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CreateSessionRequest(BaseModel):
    user_id: int | None = Field(None, description="User ID (neu da dang nhap)")
    guest_id: str | None = Field(None, description="UUID cho khach vang lai")


class CreateSessionResponse(BaseModel):
    session_id: int


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    reply: str
    intent: str
    session_id: int
    vehicle_ids: list[int] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    preferences_snapshot: dict = Field(default_factory=dict)


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    sender_type: str
    content: str
    sent_at: str


class SyncResponse(BaseModel):
    status: str
    vehicles_synced: int = 0
    message: str = ""


class MCPSourceStat(BaseModel):
    source: str
    total: int
    ratio: float
    avg_latency_ms: float | None = None


class MCPToolStat(BaseModel):
    tool: str
    total: int
    success_rate: float
    avg_latency_ms: float | None = None


class MCPTopSQLAgentQuery(BaseModel):
    query_text: str
    total: int


class MCPStatsResponse(BaseModel):
    window_days: int
    total_requests: int
    source_breakdown: list[MCPSourceStat] = Field(default_factory=list)
    tool_success: list[MCPToolStat] = Field(default_factory=list)
    top_sql_agent_queries: list[MCPTopSQLAgentQuery] = Field(default_factory=list)


ImageTag = Literal["exterior_overview", "interior", "detail_damage"]


class PricingEstimateRequest(BaseModel):
    subcategory_id: int | None = None
    subcategory_name: str | None = None
    year: int | None = None
    fuel: str | None = None
    transmission: str | None = None
    origin: str | None = None
    include_comparables: bool = False
    image_tags: list[ImageTag] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_identity(self) -> "PricingEstimateRequest":
        if self.subcategory_id is None and not (self.subcategory_name or "").strip():
            raise ValueError("Phai cung cap subcategory_id hoac subcategory_name")
        if not self.image_tags:
            raise ValueError("Phai cung cap image_tags cho tung anh")
        return self


class ScoreBreakdownOut(BaseModel):
    paint_exterior: int
    body_damage: int
    interior: int
    mechanical_visible: int
    tires_wheels: int


class DamagePercentageOut(BaseModel):
    scratch: str
    dent: str


class VehicleAssessmentOut(BaseModel):
    condition_score: int
    score_breakdown: ScoreBreakdownOut
    damage_percentage: DamagePercentageOut
    risk_flags: list[str] = Field(default_factory=list)
    damage_summary: str


class MarketDataOut(BaseModel):
    comparable_count: int
    min: int | None = None
    avg: int | None = None
    max: int | None = None


class PricingResultOut(BaseModel):
    suggested_purchase_price: int
    price_range_min: int
    price_range_max: int
    deduction_factors: list[str] = Field(default_factory=list)


class ComparableVehicleOut(BaseModel):
    id: int
    title: str
    price: int | None = None
    year: int | None = None
    fuel: str | None = None
    transmission: str | None = None
    origin: str | None = None
    status: str
    created_at: str | None = None
    priority_match: int


class PricingEstimateResponse(BaseModel):
    vehicle_assessment: VehicleAssessmentOut
    market_data: MarketDataOut
    pricing: PricingResultOut
    comparables: list[ComparableVehicleOut] | None = None
