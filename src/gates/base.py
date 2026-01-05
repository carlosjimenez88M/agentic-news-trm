"""Base gate interface and pipeline for content validation."""

from abc import ABC, abstractmethod
from typing import List, Protocol
import logging

from src.models.schemas import RawNews, GateCheckResult
from src.models.enums import GateResult

logger = logging.getLogger(__name__)


class Gate(Protocol):
    """Protocol for gate checks."""

    @property
    def name(self) -> str:
        """Gate name."""
        ...

    def check(self, article: RawNews) -> GateCheckResult:
        """Check if article passes the gate.

        Args:
            article: Raw news article

        Returns:
            GateCheckResult with pass/fail and reason
        """
        ...


class BaseGate(ABC):
    """Abstract base class for all gates."""

    def __init__(self):
        """Initialize gate."""
        self.logger = logger

    @property
    @abstractmethod
    def name(self) -> str:
        """Gate name identifier."""
        pass

    @abstractmethod
    def check(self, article: RawNews) -> GateCheckResult:
        """Check if article passes the gate.

        Args:
            article: Raw news article

        Returns:
            GateCheckResult with pass/fail and reason
        """
        pass

    def _create_result(
        self,
        article: RawNews,
        passed: bool,
        reason: str
    ) -> GateCheckResult:
        """Create a GateCheckResult.

        Args:
            article: Article being checked
            passed: Whether check passed
            reason: Reason for result

        Returns:
            GateCheckResult object
        """
        return GateCheckResult(
            article_id=article.article_id,
            gate_name=self.name,
            gate_result=GateResult.PASS if passed else GateResult.FAIL,
            gate_reason=reason
        )

    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"[{self.name}] {message}")

    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"[{self.name}] {message}")


class GatePipeline:
    """Pipeline for running multiple gates sequentially."""

    def __init__(self, gates: List[BaseGate]):
        """Initialize gate pipeline.

        Args:
            gates: List of gates to run
        """
        self.gates = gates
        self.logger = logger

    def run(self, article: RawNews) -> tuple[bool, List[GateCheckResult]]:
        """Run all gates on an article.

        Stops at first failure (fail-fast).

        Args:
            article: Article to check

        Returns:
            Tuple of (all_passed, list_of_results)
        """
        results = []

        for gate in self.gates:
            result = gate.check(article)
            results.append(result)

            if not result.passed:
                # Fail fast - stop at first failure
                self.logger.info(
                    f"Article {article.article_id} failed gate '{gate.name}': {result.gate_reason}"
                )
                return False, results

        # All gates passed
        self.logger.info(f"Article {article.article_id} passed all {len(self.gates)} gates")
        return True, results

    def run_all_gates(self, article: RawNews) -> tuple[bool, List[GateCheckResult]]:
        """Run all gates without fail-fast (for logging purposes).

        Args:
            article: Article to check

        Returns:
            Tuple of (all_passed, list_of_results)
        """
        results = []
        all_passed = True

        for gate in self.gates:
            result = gate.check(article)
            results.append(result)

            if not result.passed:
                all_passed = False

        return all_passed, results
