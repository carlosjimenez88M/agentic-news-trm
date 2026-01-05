"""Content quality gate check."""

import re
from src.gates.base import BaseGate
from src.models.schemas import RawNews, GateCheckResult
from src.config.constants import (
    MIN_CONTENT_LENGTH,
    MAX_CONTENT_LENGTH,
    REQUIRED_SPANISH_RATIO
)


class ContentQualityGate(BaseGate):
    """Gate to check content quality (length, language, completeness)."""

    @property
    def name(self) -> str:
        return "content_quality"

    def _detect_spanish_ratio(self, text: str) -> float:
        """Detect Spanish language ratio in text.

        Simple heuristic: count common Spanish words and characters.

        Args:
            text: Text to check

        Returns:
            Ratio of Spanish content (0-1)
        """
        text_lower = text.lower()

        # Common Spanish words and patterns
        spanish_indicators = [
            'el ', 'la ', 'los ', 'las ', 'de ', 'del ', 'en ', 'y ',
            'que ', 'es ', 'un ', 'una ', 'por ', 'para ', 'con ',
            'gobierno', 'presidente', 'país', 'economía', 'colombia',
            'ación', 'ción', 'dad', 'mente', 'año', 'más', 'según'
        ]

        # Count Spanish indicators
        spanish_count = sum(text_lower.count(indicator) for indicator in spanish_indicators)

        # Rough estimate: normalize by text length
        words = text_lower.split()
        if len(words) == 0:
            return 0.0

        # Spanish ratio = indicator count / total words
        ratio = min(spanish_count / len(words), 1.0)

        return ratio

    def check(self, article: RawNews) -> GateCheckResult:
        """Check content quality.

        Checks:
        1. Content length (min/max)
        2. Spanish language ratio
        3. Has title and content

        Args:
            article: Article to check

        Returns:
            GateCheckResult
        """
        # Check 1: Content length
        content_length = len(article.content)

        if content_length < MIN_CONTENT_LENGTH:
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Content too short: {content_length} < {MIN_CONTENT_LENGTH} chars"
            )

        if content_length > MAX_CONTENT_LENGTH:
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Content too long: {content_length} > {MAX_CONTENT_LENGTH} chars"
            )

        # Check 2: Spanish language ratio
        spanish_ratio = self._detect_spanish_ratio(article.content)

        if spanish_ratio < REQUIRED_SPANISH_RATIO:
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Spanish ratio too low: {spanish_ratio:.2f} < {REQUIRED_SPANISH_RATIO}"
            )

        # Check 3: Has title and content
        if not article.title or not article.title.strip():
            return self._create_result(
                article=article,
                passed=False,
                reason="Missing title"
            )

        if not article.content or not article.content.strip():
            return self._create_result(
                article=article,
                passed=False,
                reason="Missing content"
            )

        # All checks passed
        return self._create_result(
            article=article,
            passed=True,
            reason=f"Quality checks passed (length: {content_length}, spanish: {spanish_ratio:.2f})"
        )
