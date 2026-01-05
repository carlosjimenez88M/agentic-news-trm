"""Duplicate detection gate check."""

from src.gates.base import BaseGate
from src.models.schemas import RawNews, GateCheckResult
from src.storage.local_parquet import ParquetStorage
from src.config.constants import SIMILARITY_THRESHOLD


class DuplicateDetectionGate(BaseGate):
    """Gate to detect duplicate articles."""

    def __init__(self, storage: ParquetStorage):
        """Initialize duplicate detection gate.

        Args:
            storage: ParquetStorage instance for checking existing articles
        """
        super().__init__()
        self.storage = storage

    @property
    def name(self) -> str:
        return "duplicate_detection"

    def check(self, article: RawNews) -> GateCheckResult:
        """Check if article is a duplicate.

        Checks:
        1. Content hash (exact duplicate)
        2. Title similarity (fuzzy matching)

        Args:
            article: Article to check

        Returns:
            GateCheckResult
        """
        # Check 1: Exact content hash match
        if self.storage.hash_exists(article.hash_content):
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Duplicate content hash: {article.hash_content[:8]}..."
            )

        # Check 2: Similar title
        similar_titles = self.storage.find_similar_titles(
            article.title,
            threshold=SIMILARITY_THRESHOLD
        )

        if similar_titles:
            return self._create_result(
                article=article,
                passed=False,
                reason=f"Similar title found: '{similar_titles[0]}'"
            )

        # No duplicates found
        return self._create_result(
            article=article,
            passed=True,
            reason="No duplicates detected"
        )
