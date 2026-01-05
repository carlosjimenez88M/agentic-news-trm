"""Topic relevance gate check."""

from src.gates.base import BaseGate
from src.models.schemas import RawNews, GateCheckResult
from src.config.constants import (
    ALL_RELEVANT_KEYWORDS,
    MIN_KEYWORD_MATCHES
)


class TopicRelevanceGate(BaseGate):
    """Gate to check if article topic is relevant for USD/COP analysis."""

    @property
    def name(self) -> str:
        return "topic_relevance"

    def _count_keyword_matches(self, text: str) -> tuple[int, list[str]]:
        """Count how many relevant keywords are in the text.

        Args:
            text: Text to check

        Returns:
            Tuple of (count, list_of_matched_keywords)
        """
        text_lower = text.lower()
        matched_keywords = []

        for keyword in ALL_RELEVANT_KEYWORDS:
            if keyword in text_lower:
                matched_keywords.append(keyword)

        return len(matched_keywords), matched_keywords

    def check(self, article: RawNews) -> GateCheckResult:
        """Check if article is topically relevant.

        Uses keyword matching to determine if article relates to:
        - Economy, politics, security, energy, international, monetary policy

        Args:
            article: Article to check

        Returns:
            GateCheckResult
        """
        # Combine title and content for checking
        full_text = f"{article.title} {article.content}"

        # Count keyword matches
        match_count, matched_keywords = self._count_keyword_matches(full_text)

        if match_count < MIN_KEYWORD_MATCHES:
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Insufficient keyword matches: {match_count} < {MIN_KEYWORD_MATCHES}"
            )

        # Passed - article is topically relevant
        keywords_sample = matched_keywords[:5]  # Show first 5
        return self._create_result(
            article=article,
            passed=True,
            reason=f"Found {match_count} relevant keywords (e.g., {', '.join(keywords_sample)})"
        )
