"""Constants for the news analysis pipeline."""

from typing import Dict, List
from src.models.enums import TopicCategory

# Gate Check Constants
MIN_CONTENT_LENGTH = 200  # Minimum chars for article content
MAX_CONTENT_LENGTH = 50000  # Maximum chars for article content
REQUIRED_SPANISH_RATIO = 0.3  # Minimum Spanish language ratio (lowered for simple detector)
MAX_ARTICLE_AGE_HOURS = 200  # Maximum age of articles to process (increased for demo)

# Topic Relevance Keywords (for Gate 2)
TOPIC_KEYWORDS: Dict[TopicCategory, List[str]] = {
    TopicCategory.ECONOMY: [
        "economía", "económico", "dólar", "peso", "inflación", "banco",
        "comercio", "inversión", "pib", "crecimiento", "fiscal", "tributaria",
        "empleo", "desempleo", "salario", "importación", "exportación",
        "deuda", "déficit", "superávit", "mercado", "bolsa", "acciones"
    ],
    TopicCategory.POLITICS: [
        "gobierno", "petro", "congreso", "reforma", "ley", "ministro",
        "presidente", "política", "elecciones", "votación", "senado",
        "cámara", "decreto", "acuerdo", "negociación", "coalición"
    ],
    TopicCategory.SECURITY: [
        "conflicto", "farc", "eln", "seguridad", "violencia", "militar",
        "policía", "guerrilla", "disidencia", "ataque", "atentado",
        "secuestro", "narcotráfico", "droga", "paz", "acuerdo de paz"
    ],
    TopicCategory.ENERGY: [
        "petróleo", "ecopetrol", "energía", "carbón", "gas", "crudo",
        "barril", "exploración", "producción", "refinería", "oleoducto",
        "fracking", "yacimiento", "reservas", "opep", "wti", "brent"
    ],
    TopicCategory.INTERNATIONAL: [
        "venezuela", "ecuador", "brasil", "estados unidos", "china",
        "exportación", "tratado", "acuerdo comercial", "otan", "onu",
        "frontera", "migración", "diplomacia", "embajada", "trump"
    ],
    TopicCategory.MONETARY: [
        "banco de la república", "banrep", "tasa de interés", "política monetaria",
        "emisión", "reservas internacionales", "tipo de cambio", "devaluación",
        "revaluación", "intervención cambiaria", "junta directiva"
    ]
}

# Flatten all keywords for quick lookup in Gate 2
ALL_RELEVANT_KEYWORDS = [
    keyword for keywords_list in TOPIC_KEYWORDS.values()
    for keyword in keywords_list
]

MIN_KEYWORD_MATCHES = 2  # Minimum keyword matches for relevance gate

# Ranking Score Mapping
RANKING_SCORE_MAP = {
    1: "Irrelevant",
    2: "Low",
    3: "Moderate",
    4: "High",
    5: "Critical"
}

# Market Indicators Configuration
CRITICAL_INDICATORS = [
    "petroleo_brent",  # Brent oil (critical for Colombia's exports)
    "dxy",             # Dollar Index
    "usd_cop"          # USD/COP exchange rate
]

IMPORTANT_INDICATORS = [
    "vix",             # Volatility Index
    "treasury_2y",     # 2-year Treasury yield
    "treasury_10y",    # 10-year Treasury yield
    "sp500"            # S&P 500
]

CONTEXT_INDICATORS = [
    "petroleo_wti",    # WTI oil
    "gold",            # Gold price
    "coffee",          # Coffee price (Colombian export)
    "usd_mxn",         # Mexican Peso (regional context)
    "usd_brl",         # Brazilian Real (regional context)
    "usd_clp",         # Chilean Peso (regional context)
    "eur_usd"          # EUR/USD
]

# LLM Configuration
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS_PER_STEP = 2000  # Maximum output tokens per processing step
TEMPERATURE = 0.3  # Lower temperature for more consistent outputs

# Cost Tracking (prices per 1M tokens)
ANTHROPIC_INPUT_COST_PER_1M = 3.0   # $3 per 1M input tokens
ANTHROPIC_OUTPUT_COST_PER_1M = 15.0  # $15 per 1M output tokens

# Storage Configuration
PARQUET_COMPRESSION = "snappy"  # Compression for Parquet files
DATE_PARTITION_FORMAT = "date=%Y-%m-%d"  # Hive-style partitioning

# Pipeline Configuration
MAX_ARTICLES_PER_DAY = 100  # Maximum articles to process per day
SCRAPE_DELAY_SECONDS = 0.5  # Delay between scraping requests (be polite)
MAX_RETRIES = 3  # Maximum retries for failed operations
RETRY_DELAY_SECONDS = 5  # Delay between retries

# Duplication Detection
SIMILARITY_THRESHOLD = 0.9  # Threshold for fuzzy title matching (0-1)

# Common Spanish stopwords for deduplication
SPANISH_STOPWORDS = {
    "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "haber",
    "por", "con", "su", "para", "como", "estar", "tener", "le", "lo", "todo",
    "pero", "más", "hacer", "o", "poder", "decir", "este", "ir", "otro", "ese",
    "si", "me", "ya", "ver", "porque", "dar", "cuando", "él", "muy", "sin", "vez"
}
