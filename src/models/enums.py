"""Enums for the news analysis pipeline."""

from enum import Enum


class GateResult(str, Enum):
    """Result of a gate check."""
    PASS = "PASS"
    FAIL = "FAIL"


class RankingCategory(str, Enum):
    """Ranking categories for news articles (1-5 scale)."""
    IRRELEVANT = "Irrelevant"    # Score 1
    LOW = "Low"                   # Score 2
    MODERATE = "Moderate"         # Score 3
    HIGH = "High"                 # Score 4
    CRITICAL = "Critical"         # Score 5


class ProcessingStage(str, Enum):
    """Stages of the LLM processing chain."""
    SUMMARIZATION = "summarization"
    TOPIC_EXTRACTION = "topic_extraction"
    IMPACT_ANALYSIS = "impact_analysis"
    RANKING = "ranking"


class ImpactDirection(str, Enum):
    """Direction of impact on USD/COP exchange rate."""
    POSITIVE = "POSITIVE"   # Peso strengthens (USD/COP goes down)
    NEGATIVE = "NEGATIVE"   # Peso weakens (USD/COP goes up)
    NEUTRAL = "NEUTRAL"     # No clear impact


class TimeHorizon(str, Enum):
    """Time horizon for impact analysis."""
    SHORT_TERM = "short-term"     # Days to weeks
    MEDIUM_TERM = "medium-term"   # Weeks to months
    LONG_TERM = "long-term"       # Months to years


class TopicCategory(str, Enum):
    """Topic categories for news classification."""
    ECONOMY = "economy"
    POLITICS = "politics"
    SECURITY = "security"
    ENERGY = "energy"
    INTERNATIONAL = "international"
    MONETARY = "monetary"
    OTHER = "other"


class MarketTier(str, Enum):
    """Tier classification for market indicators."""
    CRITICAL = "CRITICAL"      # Tier 1: Most important
    IMPORTANT = "IMPORTANT"    # Tier 2: Important context
    CONTEXT = "CONTEXT"        # Tier 3: Additional context


class TraderAction(str, Enum):
    """Recommended action for traders based on ranking."""
    MONITOR = "monitor"    # Low priority, just keep track
    ALERT = "alert"        # Moderate to high, pay attention
    URGENT = "urgent"      # Critical, immediate attention
