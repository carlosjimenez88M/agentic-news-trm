"""Local Parquet storage with date partitioning."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from src.models.schemas import RawNews, MarketSnapshot, GateCheckResult, ProcessedNews
from src.config.constants import PARQUET_COMPRESSION
from src.utils.date_utils import get_date_partition

logger = logging.getLogger(__name__)


class ParquetStorage:
    """Handler for reading/writing Parquet files with date partitioning."""

    def __init__(self, base_dir: Path):
        """Initialize Parquet storage.

        Args:
            base_dir: Base directory for storage (e.g., data/raw)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_partition_path(
        self,
        subdirectory: str,
        date: Optional[datetime] = None
    ) -> Path:
        """Get partition path for a given date.

        Args:
            subdirectory: Subdirectory (e.g., "news", "market")
            date: Date for partition (default: today)

        Returns:
            Path to partition directory
        """
        partition = get_date_partition(date)
        path = self.base_dir / subdirectory / partition
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_filename(self, prefix: str, date: Optional[datetime] = None) -> str:
        """Generate filename with timestamp.

        Args:
            prefix: Filename prefix (e.g., "news_raw")
            date: Date for filename (default: now)

        Returns:
            Filename string
        """
        if date is None:
            date = datetime.now()

        timestamp = date.strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.parquet"

    def write_raw_news(
        self,
        articles: List[RawNews],
        date: Optional[datetime] = None
    ) -> Path:
        """Write raw news articles to Parquet.

        Args:
            articles: List of RawNews objects
            date: Date for partitioning (default: today)

        Returns:
            Path to written file
        """
        if not articles:
            logger.warning("No articles to write")
            return None

        # Convert to DataFrame
        df = pd.DataFrame([article.model_dump() for article in articles])

        # Get partition path and filename
        partition_path = self._get_partition_path("news", date)
        filename = self._get_filename("news_raw", date)
        filepath = partition_path / filename

        # Write Parquet
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression=PARQUET_COMPRESSION,
            index=False
        )

        logger.info(f"Wrote {len(articles)} articles to {filepath}")
        return filepath

    def write_market_snapshot(
        self,
        snapshot: MarketSnapshot,
        date: Optional[datetime] = None
    ) -> Path:
        """Write market snapshot to Parquet.

        Args:
            snapshot: MarketSnapshot object
            date: Date for partitioning (default: today)

        Returns:
            Path to written file
        """
        # Convert indicators to list of dicts
        records = []
        for name, indicator in snapshot.indicators.items():
            record = indicator.model_dump()
            record['snapshot_id'] = snapshot.snapshot_id
            record['snapshot_timestamp'] = snapshot.timestamp
            records.append(record)

        if not records:
            logger.warning("No market indicators to write")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(records)

        # Get partition path and filename
        partition_path = self._get_partition_path("market", date)
        filename = self._get_filename("market_snapshot", date)
        filepath = partition_path / filename

        # Write Parquet
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression=PARQUET_COMPRESSION,
            index=False
        )

        logger.info(f"Wrote {len(records)} indicators to {filepath}")
        return filepath

    def write_gate_checks(
        self,
        gate_results: List[GateCheckResult],
        date: Optional[datetime] = None
    ) -> Path:
        """Write gate check results to Parquet.

        Args:
            gate_results: List of GateCheckResult objects
            date: Date for partitioning (default: today)

        Returns:
            Path to written file
        """
        if not gate_results:
            logger.warning("No gate results to write")
            return None

        # Convert to DataFrame
        df = pd.DataFrame([result.model_dump() for result in gate_results])

        # Get partition path and filename
        # Use base_dir's parent to go to data/, then gates/
        gates_dir = self.base_dir.parent / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)

        partition = get_date_partition(date)
        partition_path = gates_dir / partition
        partition_path.mkdir(parents=True, exist_ok=True)

        filename = self._get_filename("gate_checks", date)
        filepath = partition_path / filename

        # Write Parquet
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression=PARQUET_COMPRESSION,
            index=False
        )

        logger.info(f"Wrote {len(gate_results)} gate results to {filepath}")
        return filepath

    def write_processed_news(
        self,
        processed: List[ProcessedNews],
        date: Optional[datetime] = None
    ) -> Path:
        """Write processed news to Parquet.

        Args:
            processed: List of ProcessedNews objects
            date: Date for partitioning (default: today)

        Returns:
            Path to written file
        """
        if not processed:
            logger.warning("No processed articles to write")
            return None

        # Convert to DataFrame, handling lists properly
        records = []
        for article in processed:
            record = article.model_dump()
            # Convert enum values to strings
            for key, value in record.items():
                if hasattr(value, 'value'):  # Enum
                    record[key] = value.value
                elif isinstance(value, list):  # List (e.g., topics)
                    record[key] = str(value)  # Convert to string for Parquet
            records.append(record)

        df = pd.DataFrame(records)

        # Get partition path and filename
        processed_dir = self.base_dir.parent / "processed" / "news"
        processed_dir.mkdir(parents=True, exist_ok=True)

        partition = get_date_partition(date)
        partition_path = processed_dir / partition
        partition_path.mkdir(parents=True, exist_ok=True)

        filename = self._get_filename("processed_news", date)
        filepath = partition_path / filename

        # Write Parquet
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression=PARQUET_COMPRESSION,
            index=False
        )

        logger.info(f"Wrote {len(processed)} processed articles to {filepath}")
        return filepath

    def read_raw_news(
        self,
        date: Optional[datetime] = None,
        subdirectory: str = "news"
    ) -> List[RawNews]:
        """Read raw news from Parquet.

        Args:
            date: Date partition to read (default: today)
            subdirectory: Subdirectory to read from

        Returns:
            List of RawNews objects
        """
        partition_path = self._get_partition_path(subdirectory, date)

        # Find all parquet files in partition
        parquet_files = list(partition_path.glob("*.parquet"))

        if not parquet_files:
            logger.warning(f"No parquet files found in {partition_path}")
            return []

        # Read and concatenate all files
        dfs = [pd.read_parquet(f) for f in parquet_files]
        df = pd.concat(dfs, ignore_index=True)

        # Convert to RawNews objects
        articles = [RawNews(**row) for row in df.to_dict('records')]

        logger.info(f"Read {len(articles)} articles from {partition_path}")
        return articles

    def read_market_snapshot(
        self,
        date: Optional[datetime] = None
    ) -> Optional[MarketSnapshot]:
        """Read market snapshot from Parquet.

        Args:
            date: Date partition to read (default: today)

        Returns:
            MarketSnapshot object or None if not found
        """
        partition_path = self._get_partition_path("market", date)

        # Find parquet files
        parquet_files = list(partition_path.glob("*.parquet"))

        if not parquet_files:
            logger.warning(f"No market snapshot found in {partition_path}")
            return None

        # Read latest file
        latest_file = max(parquet_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_parquet(latest_file)

        # Reconstruct MarketSnapshot (simplified - would need full reconstruction)
        logger.info(f"Read market snapshot from {latest_file}")
        return df

    def hash_exists(self, content_hash: str, date: Optional[datetime] = None) -> bool:
        """Check if a content hash exists in raw news for a given date.

        Args:
            content_hash: Content hash to check
            date: Date to check (default: today)

        Returns:
            True if hash exists
        """
        try:
            articles = self.read_raw_news(date=date)
            return any(article.hash_content == content_hash for article in articles)
        except Exception:
            return False

    def find_similar_titles(
        self,
        title: str,
        threshold: float = 0.9,
        date: Optional[datetime] = None
    ) -> List[str]:
        """Find similar titles in raw news.

        Args:
            title: Title to compare
            threshold: Similarity threshold (0-1)
            date: Date to check (default: today)

        Returns:
            List of similar titles
        """
        from src.utils.hash_utils import calculate_similarity

        try:
            articles = self.read_raw_news(date=date)
            similar = []

            for article in articles:
                similarity = calculate_similarity(title, article.title)
                if similarity >= threshold:
                    similar.append(article.title)

            return similar

        except Exception as e:
            logger.error(f"Error finding similar titles: {e}")
            return []
