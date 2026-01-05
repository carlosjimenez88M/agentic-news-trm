"""Date utilities for the pipeline."""

from datetime import datetime, timedelta
from typing import Optional


def get_today_str(fmt: str = "%Y-%m-%d") -> str:
    """Get today's date as a formatted string.

    Args:
        fmt: Date format string (default: YYYY-MM-DD)

    Returns:
        Formatted date string
    """
    return datetime.now().strftime(fmt)


def get_date_partition(date: Optional[datetime] = None) -> str:
    """Get Hive-style date partition string.

    Args:
        date: Date to partition (default: today)

    Returns:
        Partition string like "date=2025-01-05"
    """
    if date is None:
        date = datetime.now()
    return f"date={date.strftime('%Y-%m-%d')}"


def parse_date_from_url(url: str) -> Optional[datetime]:
    """Extract date from CNN article URL.

    CNN URLs have format: /YYYY/MM/DD/article-slug

    Args:
        url: Article URL

    Returns:
        Parsed datetime or None if not found
    """
    import re

    pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
    match = re.search(pattern, url)

    if match:
        year, month, day = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None

    return None


def get_article_age_hours(article_date: datetime) -> float:
    """Calculate article age in hours.

    Args:
        article_date: Article publication/scrape date

    Returns:
        Age in hours
    """
    now = datetime.now()
    delta = now - article_date
    return delta.total_seconds() / 3600


def is_within_date_range(
    date: datetime,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> bool:
    """Check if date is within a range.

    Args:
        date: Date to check
        start_date: Start of range (inclusive), None means no lower bound
        end_date: End of range (inclusive), None means no upper bound

    Returns:
        True if date is within range
    """
    if start_date and date < start_date:
        return False
    if end_date and date > end_date:
        return False
    return True


def get_date_range_days(days_back: int) -> tuple[datetime, datetime]:
    """Get a date range from N days ago to today.

    Args:
        days_back: Number of days to go back

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date
