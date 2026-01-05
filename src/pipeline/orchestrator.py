"""Main pipeline orchestrator - coordinates all components."""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.config.settings import settings
from src.scrapers.news_scraper import scrape_cnn_colombia
from src.scrapers.market_scraper import scrape_market_data
from src.gates.base import GatePipeline
from src.gates.content_quality import ContentQualityGate
from src.gates.topic_relevance import TopicRelevanceGate
from src.gates.duplicate_detection import DuplicateDetectionGate
from src.gates.temporal_relevance import TemporalRelevanceGate
from src.processors.chain_executor import ChainExecutor
from src.storage.local_parquet import ParquetStorage
from src.pipeline.cost_tracker import CostTracker
from src.pipeline.daily_analysis import generate_daily_report
from src.models.schemas import RawNews, MarketSnapshot, ProcessedNews, GateCheckResult
from src.monitoring.logger import setup_logging

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Main orchestrator for the news analysis pipeline."""

    def __init__(
        self,
        raw_data_dir: Optional[Path] = None,
        mock_llm: bool = False
    ):
        """Initialize pipeline orchestrator.

        Args:
            raw_data_dir: Directory for raw data (default: from settings)
            mock_llm: Whether to use mock LLM (for testing)
        """
        self.raw_data_dir = raw_data_dir or settings.raw_data_dir
        self.mock_llm = mock_llm

        # Initialize storage
        self.storage = ParquetStorage(self.raw_data_dir)

        # Initialize gates
        self.gate_pipeline = GatePipeline([
            ContentQualityGate(),
            TopicRelevanceGate(),
            # DuplicateDetectionGate(self.storage),  # Temporarily disabled for demo
            TemporalRelevanceGate()
        ])

        # Initialize chain executor
        self.chain_executor = ChainExecutor()

        # Initialize cost tracker
        self.cost_tracker = CostTracker()

    def run_scraping(
        self,
        max_articles: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> tuple[List[RawNews], MarketSnapshot]:
        """Run scraping phase: collect news and market data.

        Args:
            max_articles: Maximum articles to scrape (None = all)
            date: Date for storage partitioning (default: today)

        Returns:
            Tuple of (articles, market_snapshot)
        """
        logger.info("=" * 60)
        logger.info("PHASE 1: SCRAPING")
        logger.info("=" * 60)

        # Scrape news
        logger.info("Scraping news from CNN Colombia...")
        articles = scrape_cnn_colombia(
            max_articles=max_articles,
            skip_empty_content=True
        )
        logger.info(f"Scraped {len(articles)} articles")

        # Save raw news to Parquet
        if articles:
            filepath = self.storage.write_raw_news(articles, date=date)
            logger.info(f"Saved raw news to {filepath}")

        # Scrape market data
        logger.info("Scraping market data...")
        market_snapshot = scrape_market_data(include_google_finance=False)
        valid_indicators = len([i for i in market_snapshot.indicators.values() if i.error is None])
        logger.info(f"Scraped {valid_indicators}/{len(market_snapshot.indicators)} market indicators")

        # Save market snapshot to Parquet
        filepath = self.storage.write_market_snapshot(market_snapshot, date=date)
        logger.info(f"Saved market snapshot to {filepath}")

        return articles, market_snapshot

    def run_gates(
        self,
        articles: List[RawNews],
        date: Optional[datetime] = None
    ) -> tuple[List[RawNews], List[GateCheckResult]]:
        """Run gate checks phase: filter articles.

        Args:
            articles: List of raw articles
            date: Date for storage partitioning (default: today)

        Returns:
            Tuple of (passed_articles, all_gate_results)
        """
        logger.info("=" * 60)
        logger.info("PHASE 2: GATE CHECKS")
        logger.info("=" * 60)

        passed_articles = []
        all_gate_results = []

        for i, article in enumerate(articles, 1):
            logger.info(f"Checking article {i}/{len(articles)}: {article.title[:50]}...")

            # Run gates (fail-fast)
            passed, gate_results = self.gate_pipeline.run(article)

            # Collect all results
            all_gate_results.extend(gate_results)

            if passed:
                passed_articles.append(article)
                logger.info(f"  ✓ Article passed all gates")
            else:
                failed_gate = gate_results[-1]  # Last gate that failed
                logger.info(f"  ✗ Article failed gate '{failed_gate.gate_name}': {failed_gate.gate_reason}")

        # Save gate results to Parquet
        if all_gate_results:
            filepath = self.storage.write_gate_checks(all_gate_results, date=date)
            logger.info(f"Saved {len(all_gate_results)} gate results to {filepath}")

        logger.info(f"\nGate Summary: {len(passed_articles)}/{len(articles)} articles passed")

        return passed_articles, all_gate_results

    def run_processing(
        self,
        articles: List[RawNews],
        market_snapshot: MarketSnapshot,
        date: Optional[datetime] = None
    ) -> List[ProcessedNews]:
        """Run LLM processing phase: analyze articles with chain prompting.

        Args:
            articles: List of articles that passed gates
            market_snapshot: Current market context
            date: Date for storage partitioning (default: today)

        Returns:
            List of ProcessedNews objects
        """
        logger.info("=" * 60)
        logger.info("PHASE 3: LLM PROCESSING")
        logger.info("=" * 60)

        processed_articles = []

        for i, article in enumerate(articles, 1):
            logger.info(f"\nProcessing article {i}/{len(articles)}: {article.title[:60]}...")

            try:
                # Execute full chain
                processed = self.chain_executor.execute_full_chain(article, market_snapshot)

                # Track costs
                self.cost_tracker.add_processed_article(processed)

                processed_articles.append(processed)

                logger.info(
                    f"  ✓ Completed: Score={processed.ranking_score}, "
                    f"Category={processed.ranking_category.value}, "
                    f"Cost=${processed.cost_usd:.4f}"
                )

            except Exception as e:
                logger.error(f"  ✗ Failed to process article: {e}")
                continue

        # Save processed articles to Parquet
        if processed_articles:
            filepath = self.storage.write_processed_news(processed_articles, date=date)
            logger.info(f"\nSaved {len(processed_articles)} processed articles to {filepath}")

        # Generate cost report
        cost_report = self.cost_tracker.generate_report(
            date=date.strftime("%Y-%m-%d") if date else None
        )

        logger.info("\n" + "=" * 60)
        logger.info("COST REPORT")
        logger.info("=" * 60)
        logger.info(f"Total articles: {cost_report.total_articles}")
        logger.info(f"Total tokens: {cost_report.total_tokens:,}")
        logger.info(f"Total cost: ${cost_report.total_cost_usd:.4f}")
        logger.info(f"Avg cost/article: ${cost_report.avg_cost_per_article:.4f}")
        logger.info(f"Avg tokens/article: {cost_report.avg_tokens_per_article:.1f}")

        # Check cost threshold
        if settings.enable_cost_alerts:
            self.cost_tracker.check_cost_threshold(settings.daily_cost_threshold_usd)

        return processed_articles

    def run_full_pipeline(
        self,
        max_articles: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> dict:
        """Run the complete pipeline: scrape -> gates -> process -> store.

        Args:
            max_articles: Maximum articles to scrape (None = all)
            date: Date for storage partitioning (default: today)

        Returns:
            Dict with pipeline statistics
        """
        start_time = datetime.now()

        logger.info("\n" + "=" * 60)
        logger.info("STARTING FULL PIPELINE")
        logger.info("=" * 60)
        logger.info(f"Date: {date or datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"Max articles: {max_articles or 'unlimited'}")
        logger.info(f"Mock LLM: {self.mock_llm}")

        # Phase 1: Scraping
        articles, market_snapshot = self.run_scraping(max_articles=max_articles, date=date)

        if not articles:
            logger.warning("No articles scraped, stopping pipeline")
            return {
                "success": False,
                "error": "No articles scraped"
            }

        # Phase 2: Gate checks
        passed_articles, gate_results = self.run_gates(articles, date=date)

        if not passed_articles:
            logger.warning("No articles passed gates, stopping pipeline")
            return {
                "success": False,
                "error": "No articles passed gates",
                "articles_scraped": len(articles),
                "articles_passed_gates": 0
            }

        # Phase 3: LLM processing
        processed_articles = self.run_processing(passed_articles, market_snapshot, date=date)

        # Phase 4: Daily Analysis (Most Important News)
        if processed_articles:
            logger.info("\n" + "=" * 60)
            logger.info("PHASE 4: DAILY ANALYSIS")
            logger.info("=" * 60)

            try:
                daily_report = generate_daily_report(processed_articles, date=date)
                logger.info("\n" + daily_report)
            except Exception as e:
                logger.error(f"Failed to generate daily analysis: {e}")

        # Calculate statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        stats = {
            "success": True,
            "duration_seconds": duration,
            "articles_scraped": len(articles),
            "articles_passed_gates": len(passed_articles),
            "articles_processed": len(processed_articles),
            "articles_failed_processing": len(passed_articles) - len(processed_articles),
            "gate_pass_rate": len(passed_articles) / len(articles) if articles else 0,
            "total_cost_usd": self.cost_tracker.total_cost_usd,
            "avg_cost_per_article": self.cost_tracker.get_average_cost_per_article(),
            "total_tokens": self.cost_tracker.get_total_tokens()
        }

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"Articles scraped: {stats['articles_scraped']}")
        logger.info(f"Articles passed gates: {stats['articles_passed_gates']}")
        logger.info(f"Articles processed: {stats['articles_processed']}")
        logger.info(f"Gate pass rate: {stats['gate_pass_rate']:.1%}")
        logger.info(f"Total cost: ${stats['total_cost_usd']:.4f}")

        return stats


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="News analysis pipeline orchestrator")

    parser.add_argument(
        "command",
        choices=["scrape", "gate", "process", "full"],
        help="Pipeline command to run"
    )

    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Maximum number of articles to process"
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date for processing (YYYY-MM-DD), default: today"
    )

    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use mock LLM for testing"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_level=args.log_level)

    # Parse date
    date = None
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d")

    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(mock_llm=args.mock_llm)

    # Run command
    if args.command == "full":
        stats = orchestrator.run_full_pipeline(
            max_articles=args.max_articles,
            date=date
        )
        return 0 if stats["success"] else 1

    elif args.command == "scrape":
        articles, market_snapshot = orchestrator.run_scraping(
            max_articles=args.max_articles,
            date=date
        )
        logger.info(f"Scraped {len(articles)} articles")
        return 0

    elif args.command == "gate":
        # Load articles from storage
        articles = orchestrator.storage.read_raw_news(date=date)
        if not articles:
            logger.error("No articles found for gate checking")
            return 1

        passed_articles, _ = orchestrator.run_gates(articles, date=date)
        logger.info(f"{len(passed_articles)}/{len(articles)} articles passed gates")
        return 0

    elif args.command == "process":
        # Load articles and market data from storage
        articles = orchestrator.storage.read_raw_news(date=date)
        market_snapshot = orchestrator.storage.read_market_snapshot(date=date)

        if not articles:
            logger.error("No articles found for processing")
            return 1

        if market_snapshot is None:
            logger.error("No market snapshot found")
            return 1

        processed = orchestrator.run_processing(articles, market_snapshot, date=date)
        logger.info(f"Processed {len(processed)} articles")
        return 0


if __name__ == "__main__":
    exit(main())
