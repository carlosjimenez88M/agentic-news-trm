"""CNN Colombia news scraper."""

import time
from datetime import datetime
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScraperError
from src.models.schemas import RawNews
from src.utils.hash_utils import hash_content
from src.utils.retry import retry_with_backoff
from src.config.constants import SCRAPE_DELAY_SECONDS


class CNNColombiaNewsScraper(BaseScraper):
    """Scraper for CNN en Español Colombia section."""

    BASE_URL = "https://cnnespanol.cnn.com/colombia"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, timeout: int = 30):
        """Initialize CNN Colombia scraper.

        Args:
            timeout: Timeout in seconds for requests
        """
        super().__init__(timeout=timeout)

    @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a web page.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object

        Raises:
            ScraperError: If page cannot be fetched
        """
        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.timeout
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')

        except requests.RequestException as e:
            raise ScraperError(f"Error fetching page {url}: {e}")

    def _extract_article_links(self, soup: BeautifulSoup) -> List[tuple[str, str]]:
        """Extract article links from main page.

        Args:
            soup: BeautifulSoup object of main page

        Returns:
            List of (title, url) tuples
        """
        articles = []

        for link in soup.find_all('a', class_='container__link', href=True):
            href = link.get('href', '')

            # Filter only 2024-2025 articles
            if '/2025/' not in href and '/2024/' not in href:
                continue

            # Make URL absolute
            if not href.startswith('http'):
                href = f"https://cnnespanol.cnn.com{href}"

            # Extract title
            title_span = link.find('span', class_='container__headline-text')

            if title_span:
                title = title_span.get_text(strip=True)
                articles.append((title, href))

        # Remove duplicates by URL
        seen_urls = set()
        unique_articles = []
        for title, url in articles:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append((title, url))

        return unique_articles

    def _scrape_article_content(self, url: str) -> Optional[str]:
        """Scrape content from a single article page.

        Args:
            url: Article URL

        Returns:
            Article content as string, or None if failed
        """
        try:
            soup = self._fetch_page(url)

            # Extract paragraphs with class 'paragraph'
            paragraphs = soup.find_all('p', class_='paragraph')

            if not paragraphs:
                self.log_warning(f"No paragraphs found in {url}")
                return None

            content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])

            return content if content else None

        except ScraperError as e:
            self.log_error(f"Failed to scrape content from {url}: {e}")
            return None

    def scrape(
        self,
        max_articles: Optional[int] = None,
        skip_empty_content: bool = True
    ) -> List[RawNews]:
        """Scrape news articles from CNN Colombia.

        Args:
            max_articles: Maximum number of articles to scrape (None = all)
            skip_empty_content: Skip articles with empty content

        Returns:
            List of RawNews objects
        """
        self.log_info(f"Starting scrape from {self.BASE_URL}")

        # Fetch main page
        try:
            main_soup = self._fetch_page(self.BASE_URL)
        except ScraperError as e:
            self.log_error(f"Failed to fetch main page: {e}")
            return []

        # Extract article links
        article_links = self._extract_article_links(main_soup)
        self.log_info(f"Found {len(article_links)} article links")

        if max_articles:
            article_links = article_links[:max_articles]
            self.log_info(f"Limited to {max_articles} articles")

        # Scrape each article
        scraped_articles = []

        for i, (title, url) in enumerate(article_links, 1):
            self.log_info(f"Scraping article {i}/{len(article_links)}: {title}")

            # Scrape content
            content = self._scrape_article_content(url)

            # Skip if no content and skip_empty_content is True
            if skip_empty_content and not content:
                self.log_warning(f"Skipping article with empty content: {url}")
                time.sleep(SCRAPE_DELAY_SECONDS)
                continue

            # Create RawNews object
            article = RawNews(
                url=url,
                title=title,
                content=content or "",
                scraped_at=datetime.now(),
                source="CNN_Colombia",
                content_length=len(content) if content else 0,
                hash_content=hash_content(content) if content else ""
            )

            scraped_articles.append(article)

            # Be polite - delay between requests
            time.sleep(SCRAPE_DELAY_SECONDS)

        self.log_info(f"Successfully scraped {len(scraped_articles)} articles")

        return scraped_articles


def scrape_cnn_colombia(
    max_articles: Optional[int] = None,
    skip_empty_content: bool = True
) -> List[RawNews]:
    """Helper function to scrape CNN Colombia news.

    Args:
        max_articles: Maximum number of articles to scrape
        skip_empty_content: Skip articles with empty content

    Returns:
        List of RawNews objects
    """
    scraper = CNNColombiaNewsScraper()
    return scraper.scrape(
        max_articles=max_articles,
        skip_empty_content=skip_empty_content
    )
