"""Market data scrapers for Yahoo Finance and Google Finance."""

from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import yfinance as yf

from src.scrapers.base import BaseScraper, ScraperError
from src.models.schemas import MarketIndicator, MarketSnapshot
from src.models.enums import MarketTier
from src.utils.retry import retry_with_backoff
from src.config.constants import (
    CRITICAL_INDICATORS,
    IMPORTANT_INDICATORS,
    CONTEXT_INDICATORS
)


class YahooFinanceMarketScraper(BaseScraper):
    """Scraper for market data from Yahoo Finance."""

    # Indicator configuration with symbols and tiers
    INDICATORS_CONFIG = {
        # Critical indicators
        "petroleo_brent": {"symbol": "BZ=F", "tier": MarketTier.CRITICAL},
        "dxy": {"symbol": "DX-Y.NYB", "tier": MarketTier.CRITICAL},
        "usd_cop": {"symbol": "COP=X", "tier": MarketTier.CRITICAL},

        # Important indicators
        "vix": {"symbol": "^VIX", "tier": MarketTier.IMPORTANT},
        "treasury_10y": {"symbol": "^TNX", "tier": MarketTier.IMPORTANT},
        "treasury_2y": {"symbol": "^IRX", "tier": MarketTier.IMPORTANT},
        "sp500": {"symbol": "^GSPC", "tier": MarketTier.IMPORTANT},

        # Context indicators
        "petroleo_wti": {"symbol": "CL=F", "tier": MarketTier.CONTEXT},
        "oro": {"symbol": "GC=F", "tier": MarketTier.CONTEXT},
        "cafe": {"symbol": "KC=F", "tier": MarketTier.CONTEXT},
        "usd_mxn": {"symbol": "MXN=X", "tier": MarketTier.CONTEXT},
        "usd_brl": {"symbol": "BRL=X", "tier": MarketTier.CONTEXT},
        "usd_clp": {"symbol": "CLP=X", "tier": MarketTier.CONTEXT},
        "eur_usd": {"symbol": "EURUSD=X", "tier": MarketTier.CONTEXT},
    }

    def _fetch_single_indicator(
        self,
        name: str,
        symbol: str,
        tier: MarketTier
    ) -> MarketIndicator:
        """Fetch data for a single market indicator.

        Args:
            name: Indicator name
            symbol: Yahoo Finance symbol
            tier: Market tier classification

        Returns:
            MarketIndicator object
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info

            price = info.last_price
            prev_close = info.previous_close

            if price is None:
                return MarketIndicator(
                    name=name,
                    symbol=symbol,
                    tier=tier,
                    timestamp=datetime.now(),
                    error="No price data available"
                )

            # Calculate changes
            change_value = None
            change_pct = None

            if prev_close and prev_close > 0:
                change_value = price - prev_close
                change_pct = (change_value / prev_close) * 100

            return MarketIndicator(
                name=name,
                symbol=symbol,
                value=round(price, 4),
                previous_close=round(prev_close, 4) if prev_close else None,
                change_value=round(change_value, 4) if change_value else None,
                change_pct=round(change_pct, 2) if change_pct else None,
                tier=tier,
                timestamp=datetime.now(),
                error=None
            )

        except Exception as e:
            self.log_error(f"Error fetching {name} ({symbol}): {e}")
            return MarketIndicator(
                name=name,
                symbol=symbol,
                tier=tier,
                timestamp=datetime.now(),
                error=str(e)
            )

    def scrape(self, indicators: Optional[List[str]] = None) -> MarketSnapshot:
        """Scrape market indicators.

        Args:
            indicators: List of indicator names to scrape (None = all)

        Returns:
            MarketSnapshot with all indicators
        """
        self.log_info("Starting market data scrape from Yahoo Finance")

        # Determine which indicators to scrape
        if indicators is None:
            indicators_to_scrape = self.INDICATORS_CONFIG
        else:
            indicators_to_scrape = {
                k: v for k, v in self.INDICATORS_CONFIG.items()
                if k in indicators
            }

        # Fetch all indicators
        scraped_indicators = {}

        for name, config in indicators_to_scrape.items():
            self.log_info(f"Fetching {name} ({config['symbol']})")

            indicator = self._fetch_single_indicator(
                name=name,
                symbol=config['symbol'],
                tier=config['tier']
            )

            scraped_indicators[name] = indicator

        # Create snapshot
        snapshot = MarketSnapshot(
            timestamp=datetime.now(),
            indicators=scraped_indicators
        )

        valid_count = len([i for i in scraped_indicators.values() if i.error is None])
        self.log_info(f"Successfully scraped {valid_count}/{len(scraped_indicators)} indicators")

        return snapshot

    def scrape_critical_only(self) -> MarketSnapshot:
        """Scrape only critical indicators.

        Returns:
            MarketSnapshot with critical indicators only
        """
        critical_names = [
            name for name, config in self.INDICATORS_CONFIG.items()
            if config['tier'] == MarketTier.CRITICAL
        ]
        return self.scrape(indicators=critical_names)


class GoogleFinanceExchangeScraper(BaseScraper):
    """Scraper for exchange rates from Google Finance."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    EXCHANGE_RATES = {
        "usd_cop": "https://www.google.com/finance/quote/USD-COP",
        "eur_cop": "https://www.google.com/finance/quote/EUR-COP",
    }

    @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a Google Finance page.

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

    def _parse_price(self, soup: BeautifulSoup) -> float:
        """Parse price from Google Finance page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Price as float

        Raises:
            ScraperError: If price cannot be parsed
        """
        element = soup.find("div", class_="YMlKec fxKbKc")

        if element is None:
            raise ScraperError("Price element not found on page")

        price_text = element.text.strip()
        price_clean = price_text.replace("$", "").replace(",", "")

        try:
            return float(price_clean)
        except ValueError:
            raise ScraperError(f"Could not convert price: {price_text}")

    def scrape_exchange_rate(self, pair: str) -> MarketIndicator:
        """Scrape a single exchange rate.

        Args:
            pair: Exchange pair name (e.g., "usd_cop")

        Returns:
            MarketIndicator object
        """
        if pair not in self.EXCHANGE_RATES:
            raise ValueError(f"Unknown exchange pair: {pair}")

        url = self.EXCHANGE_RATES[pair]
        self.log_info(f"Scraping {pair} from Google Finance")

        try:
            soup = self._fetch_page(url)
            price = self._parse_price(soup)

            return MarketIndicator(
                name=pair,
                symbol=pair.upper().replace("_", "/"),
                value=round(price, 4),
                tier=MarketTier.CRITICAL,
                timestamp=datetime.now(),
                error=None
            )

        except (ScraperError, Exception) as e:
            self.log_error(f"Failed to scrape {pair}: {e}")
            return MarketIndicator(
                name=pair,
                symbol=pair.upper().replace("_", "/"),
                tier=MarketTier.CRITICAL,
                timestamp=datetime.now(),
                error=str(e)
            )

    def scrape(self) -> Dict[str, MarketIndicator]:
        """Scrape all configured exchange rates.

        Returns:
            Dictionary of MarketIndicator objects
        """
        self.log_info("Starting exchange rate scrape from Google Finance")

        indicators = {}

        for pair in self.EXCHANGE_RATES.keys():
            indicator = self.scrape_exchange_rate(pair)
            indicators[pair] = indicator

        return indicators


def scrape_market_data(include_google_finance: bool = False) -> MarketSnapshot:
    """Helper function to scrape all market data.

    Args:
        include_google_finance: Whether to include Google Finance data

    Returns:
        MarketSnapshot with all indicators
    """
    # Scrape Yahoo Finance data
    yahoo_scraper = YahooFinanceMarketScraper()
    snapshot = yahoo_scraper.scrape()

    # Optionally add Google Finance data (for comparison)
    if include_google_finance:
        google_scraper = GoogleFinanceExchangeScraper()
        google_indicators = google_scraper.scrape()

        # Add with prefix to avoid conflicts
        for name, indicator in google_indicators.items():
            snapshot.indicators[f"google_{name}"] = indicator

    return snapshot


def scrape_critical_market_data() -> MarketSnapshot:
    """Helper function to scrape only critical market indicators.

    Returns:
        MarketSnapshot with critical indicators
    """
    scraper = YahooFinanceMarketScraper()
    return scraper.scrape_critical_only()
