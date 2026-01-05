"""Temporal relevance gate check."""

from datetime import datetime
from src.gates.base import BaseGate
from src.models.schemas import RawNews, GateCheckResult
from src.utils.date_utils import parse_date_from_url, get_article_age_hours
from src.config.constants import MAX_ARTICLE_AGE_HOURS


class TemporalRelevanceGate(BaseGate):
    """Gate to check if article is recent enough."""

    @property
    def name(self) -> str:
        return "temporal_relevance"

    def check(self, article: RawNews) -> GateCheckResult:
        """Check if article is temporally relevant (not too old).

        Tries to extract date from URL first, falls back to scraped_at.

        Args:
            article: Article to check

        Returns:
            GateCheckResult
        """
        # Try to extract date from URL
        article_date = parse_date_from_url(article.url)

        # Fallback to scraped_at if no date in URL
        if article_date is None:
            article_date = article.scraped_at
            date_source = "scraped_at"
        else:
            date_source = "URL"

        # Calculate age in hours
        age_hours = get_article_age_hours(article_date)

        # Check if too old
        if age_hours > MAX_ARTICLE_AGE_HOURS:
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Article too old: {age_hours:.1f} hours (max: {MAX_ARTICLE_AGE_HOURS}, source: {date_source})"
            )

        # Recent enough
        return self._create_result(
            article=article,
            passed=True,
            reason=f"Article is recent: {age_hours:.1f} hours old (source: {date_source})"
        )
