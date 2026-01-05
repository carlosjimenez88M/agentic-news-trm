"""Cost tracking for LLM API usage."""

import logging
from typing import List
from dataclasses import dataclass, field
from datetime import datetime

from src.models.schemas import ProcessedNews
from src.config.constants import (
    ANTHROPIC_INPUT_COST_PER_1M,
    ANTHROPIC_OUTPUT_COST_PER_1M
)

logger = logging.getLogger(__name__)


@dataclass
class CostReport:
    """Report of costs for a pipeline run."""

    date: str
    total_articles: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_tokens_per_article: float = 0.0
    avg_cost_per_article: float = 0.0
    min_cost_article: float = 0.0
    max_cost_article: float = 0.0
    processing_time_ms: int = 0
    cost_breakdown: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "date": self.date,
            "total_articles": self.total_articles,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_tokens_per_article": round(self.avg_tokens_per_article, 2),
            "avg_cost_per_article": round(self.avg_cost_per_article, 4),
            "min_cost_article": round(self.min_cost_article, 4),
            "max_cost_article": round(self.max_cost_article, 4),
            "processing_time_ms": self.processing_time_ms,
            "cost_breakdown": self.cost_breakdown
        }


class CostTracker:
    """Tracker for LLM API costs and token usage."""

    def __init__(self):
        """Initialize cost tracker."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.article_costs: List[dict] = []

    def add_processed_article(self, processed: ProcessedNews):
        """Add a processed article to tracking.

        Args:
            processed: ProcessedNews object
        """
        input_tokens = processed.input_tokens
        output_tokens = processed.output_tokens
        cost_usd = processed.cost_usd

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost_usd

        self.article_costs.append({
            "article_id": processed.article_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": processed.total_tokens,
            "cost_usd": cost_usd,
            "ranking_score": processed.ranking_score,
            "processing_time_ms": processed.processing_time_ms
        })

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return self.total_input_tokens + self.total_output_tokens

    def get_average_cost_per_article(self) -> float:
        """Get average cost per article."""
        if not self.article_costs:
            return 0.0
        return self.total_cost_usd / len(self.article_costs)

    def get_average_tokens_per_article(self) -> float:
        """Get average tokens per article."""
        if not self.article_costs:
            return 0.0
        return self.get_total_tokens() / len(self.article_costs)

    def generate_report(self, date: str = None) -> CostReport:
        """Generate cost report.

        Args:
            date: Date string for report (default: today)

        Returns:
            CostReport object
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if not self.article_costs:
            logger.warning("No articles tracked, returning empty report")
            return CostReport(date=date)

        costs = [a["cost_usd"] for a in self.article_costs]
        total_processing_time = sum(a["processing_time_ms"] for a in self.article_costs)

        report = CostReport(
            date=date,
            total_articles=len(self.article_costs),
            total_input_tokens=self.total_input_tokens,
            total_output_tokens=self.total_output_tokens,
            total_tokens=self.get_total_tokens(),
            total_cost_usd=self.total_cost_usd,
            avg_tokens_per_article=self.get_average_tokens_per_article(),
            avg_cost_per_article=self.get_average_cost_per_article(),
            min_cost_article=min(costs),
            max_cost_article=max(costs),
            processing_time_ms=total_processing_time,
            cost_breakdown=self.article_costs
        )

        logger.info(
            f"Cost report generated: {report.total_articles} articles, "
            f"${report.total_cost_usd:.4f} total cost, "
            f"${report.avg_cost_per_article:.4f} avg cost/article"
        )

        return report

    def check_cost_threshold(self, threshold_usd: float) -> bool:
        """Check if total cost exceeds threshold.

        Args:
            threshold_usd: Cost threshold in USD

        Returns:
            True if cost exceeds threshold
        """
        if self.total_cost_usd > threshold_usd:
            logger.warning(
                f"Cost threshold exceeded: ${self.total_cost_usd:.4f} > ${threshold_usd:.2f}"
            )
            return True
        return False

    def reset(self):
        """Reset tracker for new run."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.article_costs = []
        logger.info("Cost tracker reset")


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for given token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    input_cost = (input_tokens / 1_000_000) * ANTHROPIC_INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * ANTHROPIC_OUTPUT_COST_PER_1M
    return input_cost + output_cost
