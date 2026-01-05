"""Pydantic schemas for the news analysis pipeline."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from src.models.enums import (
    GateResult, RankingCategory, ProcessingStage,
    ImpactDirection, TimeHorizon, TopicCategory,
    MarketTier, TraderAction
)


# ============================================================================
# Raw Data Models
# ============================================================================

class RawNews(BaseModel):
    """Schema for raw news articles scraped from sources."""

    article_id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    title: str
    content: str
    scraped_at: datetime = Field(default_factory=datetime.now)
    source: str = "CNN_Colombia"
    content_length: int = Field(default=0)
    hash_content: str = Field(default="")
    date_partition: str = Field(default="")

    @field_validator("content_length", mode="before")
    @classmethod
    def compute_content_length(cls, v, info):
        """Compute content length from content field."""
        if v == 0 and "content" in info.data:
            return len(info.data["content"])
        return v

    @field_validator("date_partition", mode="before")
    @classmethod
    def compute_date_partition(cls, v, info):
        """Compute date partition from scraped_at."""
        if not v and "scraped_at" in info.data:
            scraped_at = info.data["scraped_at"]
            if isinstance(scraped_at, str):
                scraped_at = datetime.fromisoformat(scraped_at)
            return scraped_at.strftime("%Y-%m-%d")
        return v

    model_config = {"frozen": False}


class MarketIndicator(BaseModel):
    """Schema for a single market indicator."""

    name: str
    symbol: str
    value: float
    previous_close: Optional[float] = None
    change_value: Optional[float] = None
    change_pct: Optional[float] = None
    tier: MarketTier
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None

    model_config = {"frozen": False}


class MarketSnapshot(BaseModel):
    """Schema for a complete market snapshot at a point in time."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    indicators: Dict[str, MarketIndicator] = Field(default_factory=dict)
    date_partition: str = Field(default="")

    @field_validator("date_partition", mode="before")
    @classmethod
    def compute_date_partition(cls, v, info):
        """Compute date partition from timestamp."""
        if not v and "timestamp" in info.data:
            timestamp = info.data["timestamp"]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            return timestamp.strftime("%Y-%m-%d")
        return v

    def get_indicator_value(self, name: str) -> Optional[float]:
        """Get value of an indicator by name."""
        indicator = self.indicators.get(name)
        return indicator.value if indicator else None

    def to_context_string(self) -> str:
        """Convert market snapshot to formatted string for LLM context."""
        lines = []
        for name, indicator in self.indicators.items():
            change_str = f"({indicator.change_pct:+.2f}%)" if indicator.change_pct else ""
            lines.append(f"{name}: {indicator.value:.2f} {change_str}")
        return "\n".join(lines)

    model_config = {"frozen": False}


# ============================================================================
# Gate Check Models
# ============================================================================

class GateCheckResult(BaseModel):
    """Result of a gate check on an article."""

    article_id: str
    gate_name: str
    gate_result: GateResult
    gate_reason: str
    checked_at: datetime = Field(default_factory=datetime.now)
    date_partition: str = Field(default="")

    @field_validator("date_partition", mode="before")
    @classmethod
    def compute_date_partition(cls, v, info):
        """Compute date partition from checked_at."""
        if not v and "checked_at" in info.data:
            checked_at = info.data["checked_at"]
            if isinstance(checked_at, str):
                checked_at = datetime.fromisoformat(checked_at)
            return checked_at.strftime("%Y-%m-%d")
        return v

    @property
    def passed(self) -> bool:
        """Check if gate passed."""
        return self.gate_result == GateResult.PASS

    model_config = {"frozen": False}


# ============================================================================
# LLM Processing Models (Chain Outputs)
# ============================================================================

class SummarizationOutput(BaseModel):
    """Output from Step 1: Summarization."""

    summary: str
    cot_reasoning: str

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v):
        """Ensure summary is not empty."""
        if not v or len(v.strip()) < 10:
            raise ValueError("Summary must be at least 10 characters")
        return v.strip()


class TopicExtractionOutput(BaseModel):
    """Output from Step 2: Topic Extraction."""

    topics: List[TopicCategory]
    cot_reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v):
        """Ensure at least one topic is extracted."""
        if not v:
            raise ValueError("At least one topic must be extracted")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class ImpactAnalysisOutput(BaseModel):
    """Output from Step 3: Impact Analysis."""

    direction: ImpactDirection
    mechanisms: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    time_horizon: TimeHorizon
    cot_reasoning: str

    @field_validator("mechanisms")
    @classmethod
    def validate_mechanisms(cls, v):
        """Ensure at least one mechanism is identified."""
        if not v:
            raise ValueError("At least one impact mechanism must be identified")
        return v


class RankingOutput(BaseModel):
    """Output from Step 4: Ranking."""

    score: int = Field(ge=1, le=5)
    category: RankingCategory
    justification: str
    trader_action: TraderAction
    cot_reasoning: str

    @field_validator("score")
    @classmethod
    def validate_score(cls, v):
        """Ensure score is 1-5."""
        if not 1 <= v <= 5:
            raise ValueError("Score must be between 1 and 5")
        return v

    @field_validator("justification")
    @classmethod
    def validate_justification(cls, v):
        """Ensure justification is meaningful."""
        if not v or len(v.strip()) < 20:
            raise ValueError("Justification must be at least 20 characters")
        return v.strip()


class ProcessedNews(BaseModel):
    """Complete processed news article with all chain outputs."""

    article_id: str
    processing_stage: ProcessingStage
    chain_step: int = Field(ge=1, le=4)

    # Metadata
    input_tokens: int = 0
    output_tokens: int = 0
    processing_time_ms: int = 0
    processed_at: datetime = Field(default_factory=datetime.now)

    # Chain outputs (stored as JSON strings in Parquet)
    summary: Optional[str] = None
    summary_cot: Optional[str] = None

    topics: Optional[List[TopicCategory]] = None
    topics_cot: Optional[str] = None
    topics_confidence: Optional[float] = None

    impact_direction: Optional[ImpactDirection] = None
    impact_mechanisms: Optional[List[str]] = None
    impact_confidence: Optional[float] = None
    impact_time_horizon: Optional[TimeHorizon] = None
    impact_cot: Optional[str] = None

    ranking_score: Optional[int] = None
    ranking_category: Optional[RankingCategory] = None
    ranking_justification: Optional[str] = None
    ranking_trader_action: Optional[TraderAction] = None
    ranking_cot: Optional[str] = None

    # Partition key
    date_partition: str = Field(default="")

    @field_validator("date_partition", mode="before")
    @classmethod
    def compute_date_partition(cls, v, info):
        """Compute date partition from processed_at."""
        if not v and "processed_at" in info.data:
            processed_at = info.data["processed_at"]
            if isinstance(processed_at, str):
                processed_at = datetime.fromisoformat(processed_at)
            return processed_at.strftime("%Y-%m-%d")
        return v

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        """Calculate cost in USD."""
        from src.config.constants import (
            ANTHROPIC_INPUT_COST_PER_1M,
            ANTHROPIC_OUTPUT_COST_PER_1M
        )
        input_cost = (self.input_tokens / 1_000_000) * ANTHROPIC_INPUT_COST_PER_1M
        output_cost = (self.output_tokens / 1_000_000) * ANTHROPIC_OUTPUT_COST_PER_1M
        return input_cost + output_cost

    model_config = {"frozen": False}


# ============================================================================
# Aggregation Models
# ============================================================================

class DailySummary(BaseModel):
    """Daily aggregated summary of processed articles."""

    date: str
    articles_scraped: int
    articles_passed_gates: int
    articles_failed_gates: int
    articles_processed: int
    articles_failed_processing: int

    # Token usage
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float

    # Ranking distribution
    ranking_distribution: Dict[int, int] = Field(default_factory=dict)  # score -> count

    # Topic distribution
    topic_distribution: Dict[str, int] = Field(default_factory=dict)  # topic -> count

    # Top articles
    critical_articles: List[str] = Field(default_factory=list)  # article_ids with score=5
    high_priority_articles: List[str] = Field(default_factory=list)  # article_ids with score=4

    # Processing stats
    avg_processing_time_ms: float = 0.0
    total_processing_time_ms: int = 0

    # Gate breakdown
    gate_failures: Dict[str, int] = Field(default_factory=dict)  # gate_name -> fail_count

    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {"frozen": False}


# ============================================================================
# Pipeline State Model (for LangGraph)
# ============================================================================

class PipelineState(BaseModel):
    """State for LangGraph processing pipeline."""

    # Input
    article_id: str
    raw_news: RawNews
    market_context: MarketSnapshot

    # Step outputs
    step: int = 0
    summarization: Optional[SummarizationOutput] = None
    topic_extraction: Optional[TopicExtractionOutput] = None
    impact_analysis: Optional[ImpactAnalysisOutput] = None
    ranking: Optional[RankingOutput] = None

    # Metadata
    tokens_used: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.step >= 4 and self.ranking is not None

    @property
    def has_errors(self) -> bool:
        """Check if pipeline has errors."""
        return len(self.errors) > 0

    model_config = {"frozen": False, "arbitrary_types_allowed": True}
