"""
Schemas cho internal vehicle pricing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


AllowedRole = Literal["MANAGER", "ADMIN"]
ImageSource = Literal["cloudinary"]
DeclaredImageGroup = Literal[
    "front",
    "rear",
    "left_side",
    "right_side",
    "interior_front",
    "interior_rear",
    "dashboard",
    "odometer",
    "engine_bay",
    "tire",
    "damage_detail",
    "document",
    "other",
]
ResultType = Literal[
    "standard_estimate",
    "variant_uncertain_estimate",
    "low_data_model_estimate",
    "taxonomy_fallback_estimate",
    "rough_segment_estimate",
    "insufficient_market_data",
]


class RequestedBy(BaseModel):
    userId: int = Field(..., gt=0)
    username: str | None = None
    role: AllowedRole
    branchId: int | None = Field(None, gt=0)


class VehicleInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    categoryId: int = Field(..., gt=0)
    subcategoryId: int = Field(..., gt=0)
    year: int = Field(..., ge=1980, le=2100)
    mileage: int = Field(..., ge=0)
    fuel: str = Field(..., min_length=1, max_length=100)
    transmission: str = Field(..., min_length=1, max_length=100)
    bodyStyle: str | None = Field(None, max_length=100)
    origin: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=5000)


class ImageAsset(BaseModel):
    url: HttpUrl
    publicId: str = Field(..., min_length=1, max_length=500)
    source: ImageSource
    declaredGroup: DeclaredImageGroup
    caption: str | None = Field(None, max_length=1000)
    captionBy: str | None = Field(None, max_length=100)
    captionType: str | None = Field(None, max_length=100)


class InternalPricingEstimateRequest(BaseModel):
    requestId: str = Field(..., min_length=1, max_length=100)
    requestedBy: RequestedBy
    vehicleInput: VehicleInput
    imageAssets: list[ImageAsset] = Field(..., min_length=1)


class DataBasisOut(BaseModel):
    source: str
    type: str
    note: str


class VehicleUnderstandingOut(BaseModel):
    detectedBrand: str | None = None
    detectedModel: str | None = None
    brandKeyword: str | None = None
    modelKeyword: str | None = None
    detectedVariant: str | None = None
    variantConfidence: float
    normalizedFuel: str
    normalizedTransmission: str
    taxonomyMismatch: bool = False
    taxonomyWarning: str | None = None
    warning: str | None = None


class PriceBandOut(BaseModel):
    suggestedPrice: int | None = None
    minPrice: int | None = None
    maxPrice: int | None = None
    label: str


class PricingBreakdownOut(BaseModel):
    marketMedianPrice: int | None = None
    conditionAdjustment: int = 0
    visualAdjustment: int = 0
    trustAdjustment: int = 0
    baseReconditioningCost: int = 0
    damageRepairCost: int = 0
    estimatedReconditioningCost: int = 0
    riskBuffer: int = 0
    targetMargin: int = 0


class ConditionAssessmentOut(BaseModel):
    overallScore: float
    label: str
    confidence: float
    visibleDamage: bool
    carQualityScore: int
    exteriorScore: int | None = None
    interiorScore: int | None = None
    engineBayScore: int | None = None
    damageFindings: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RiskAssessmentOut(BaseModel):
    riskScore: int
    riskLevel: str
    direction: str = "higher_is_riskier"
    riskFlags: list[dict] = Field(default_factory=list)


class TrustAssessmentOut(BaseModel):
    trustScore: float
    trustLabel: str
    direction: str = "higher_is_more_trustworthy"
    trustFlags: list[dict] = Field(default_factory=list)


class ImageProcessingOut(BaseModel):
    uploadedCount: int
    validImageCount: int
    exactDuplicatesRemoved: int
    nearDuplicatesRemoved: int
    analyzedCount: int
    groups: dict[str, int] = Field(default_factory=dict)
    coveredViews: list[str] = Field(default_factory=list)
    partialViews: list[str] = Field(default_factory=list)
    missingViews: list[str] = Field(default_factory=list)
    incompleteViews: list[dict] = Field(default_factory=list)
    inspectionGroups: list[str] = Field(default_factory=list)
    ignoredImages: list[dict] = Field(default_factory=list)


class MarketStatsOut(BaseModel):
    similarListingsFound: int
    similarListingsUsed: int
    sampleSize: int = 0
    effectiveSampleSize: float = 0
    totalWeight: float = 0
    statisticalStrength: str = "low"
    observedMinPrice: int | None = None
    observedMaxPrice: int | None = None
    outliersRemoved: int = 0
    priceStatisticMethod: str | None = None
    rawMedianPrice: int | None = None
    medianPrice: int | None = None
    p25Price: int | None = None
    p75Price: int | None = None
    weightedMedianPrice: int | None = None
    weightedP25Price: int | None = None
    weightedP75Price: int | None = None
    weightedMedianNote: str | None = None
    averageSimilarityScore: float = 0
    note: str | None = None
    marketWindowDays: int


class FallbackOut(BaseModel):
    level: int
    used: bool
    description: str


class MarketSearchOut(BaseModel):
    toolName: str
    marketWindowDays: int
    fallbackWindowUsed: bool
    fallbackLevel: int
    inputCategoryId: int
    inputSubcategoryId: int
    inputCategoryName: str | None = None
    inputSubcategoryName: str | None = None
    selectedAttemptLevel: int | None = None
    finalSampleSize: int = 0
    effectiveSampleSize: float = 0
    totalWeight: float = 0
    fallbackReason: str | None = None
    marketWindow: dict = Field(default_factory=dict)
    rawCount: int = 0
    scoredCount: int = 0
    eligibleCount: int = 0
    usedCount: int = 0
    outliersRemoved: int = 0
    attempts: list[dict] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    similarListingsFound: int = 0
    similarListingsUsed: int = 0


class ExpertExplanationOut(BaseModel):
    summary: str
    marketReasoning: list[str] = Field(default_factory=list)
    conditionReasoning: list[str] = Field(default_factory=list)
    purchaseReasoning: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommendedNextActions: list[str] = Field(default_factory=list)


class InternalPricingEstimateResponse(BaseModel):
    valuationId: str
    resultType: ResultType
    resultFlags: list[str] = Field(default_factory=list)
    dataBasis: DataBasisOut
    vehicleUnderstanding: VehicleUnderstandingOut
    marketReferencePrice: dict
    fairPrice: dict
    dealSuggestion: dict
    marketSellingPrice: PriceBandOut
    purchasePrice: PriceBandOut
    roughPurchaseRange: dict | None = None
    pricingBreakdown: PricingBreakdownOut
    conditionAssessment: ConditionAssessmentOut
    riskAssessment: RiskAssessmentOut
    trustAssessment: TrustAssessmentOut
    imageProcessing: ImageProcessingOut
    damageList: list[dict] = Field(default_factory=list)
    pricingAdjustments: list[dict] = Field(default_factory=list)
    topComparablesUsed: list[dict] = Field(default_factory=list)
    marketSearch: MarketSearchOut
    marketStats: MarketStatsOut
    fallback: FallbackOut
    confidence: float
    confidenceLabel: str
    confidenceWarnings: list[str] = Field(default_factory=list)
    confidenceBreakdown: dict = Field(default_factory=dict)
    variantMatchCoverage: dict = Field(default_factory=dict)
    imageCaptionAnalysis: dict = Field(default_factory=dict)
    businessWarnings: list[str] = Field(default_factory=list)
    internalDiagnostics: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    expertExplanation: ExpertExplanationOut


class PersistenceEnvelope(BaseModel):
    schemaVersion: str
    source: str
    status: str
    requestId: str
    requestedBy: dict
    input: dict
    dataBasis: dict
    textAnalysis: dict
    imageProcessing: dict
    imageAnalysis: dict
    inspection: dict | None = None
    marketSearch: dict
    marketStats: dict
    pricingBreakdown: dict
    pricingAdjustments: list[dict] | None = None
    fairPrice: dict | None = None
    dealSuggestion: dict | None = None
    result: dict
    expertExplanation: dict
    warnings: list[str]
    aiUsage: dict
    createdAt: str

    @model_validator(mode="after")
    def validate_status(self) -> "PersistenceEnvelope":
        if self.status not in {"completed", "failed"}:
            raise ValueError("status khong hop le")
        return self
