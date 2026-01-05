# AI Agentic News Analysis for USD/COP Exchange Rate

An AI-powered MLOps pipeline that analyzes Colombian news to assess their impact on the USD/COP exchange rate. Uses Claude AI with Chain-of-Thought prompting, gate checks for cost optimization, and automated data processing.

## Project Overview

This system:
- **Scrapes** Colombian news from CNN en Español and market data from Yahoo Finance
- **Filters** irrelevant content using 4 gate checks (~70% cost savings)
- **Analyzes** news with Claude AI using 4-step chain prompting with COT reasoning
- **Ranks** news by relevance (1-5 scale) for USD/COP traders
- **Stores** all data in Parquet format with date partitioning
- **Automates** daily execution via GitHub Actions

### Key Features

- **Chain Prompting with COT**: 4-step analysis (Summarization → Topics → Impact → Ranking)
- **Gate Checks**: Content quality, topic relevance, duplicate detection, temporal relevance
- **Cost Tracking**: Token usage and cost monitoring (~$0.90/day for 15 articles)
- **MLOps Ready**: Parquet storage, partitioning, structured logging, reproducibility
- **Modular Architecture**: Clean separation of concerns, testable components

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY EXECUTION                           │
│                  (GitHub Actions)                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: SCRAPING                                           │
│  • CNN Colombia News → data/raw/news/date=YYYY-MM-DD/        │
│  • Yahoo Finance Market Data → data/raw/market/              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: GATE CHECKS (Fail Fast)                            │
│  1. Content Quality (length, language)                       │
│  2. Topic Relevance (keyword matching)                       │
│  3. Duplicate Detection (hash + fuzzy title)                 │
│  4. Temporal Relevance (max 48 hours old)                    │
│  → PASS (~30%) → Continue                                    │
│  → FAIL (~70%) → Skip (save LLM costs)                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: LLM PROCESSING (Claude Sonnet 4.5)                 │
│  Step 1: Summarization (with COT)                            │
│  Step 2: Topic Extraction (economy/politics/security/etc)    │
│  Step 3: Impact Analysis (USD/COP direction + mechanisms)    │
│  Step 4: Ranking (1-5: Irrelevant → Critical)                │
│  → data/processed/news/date=YYYY-MM-DD/                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STORAGE & REPORTING                                          │
│  • Parquet files with Snappy compression                     │
│  • Cost report (tokens, USD, breakdown)                      │
│  • Structured logs (JSON/text format)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key

### Setup

1. **Install uv** (ultra-fast Python package manager):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Clone and setup**:

```bash
git clone <repository-url>
cd agentic-news-trm
uv sync  # Installs all dependencies
```

3. **Configure environment**:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

---

## Usage

### Run Full Pipeline

```bash
# Run complete pipeline (scrape → gates → process)
uv run python -m src.pipeline.orchestrator full

# Limit to 10 articles for testing
uv run python -m src.pipeline.orchestrator full --max-articles 10

# Use mock LLM (no API costs)
uv run python -m src.pipeline.orchestrator full --mock-llm
```

### Run Individual Phases

```bash
# Phase 1: Scraping only
uv run python -m src.pipeline.orchestrator scrape --max-articles 20

# Phase 2: Gate checks (requires scraped data)
uv run python -m src.pipeline.orchestrator gate

# Phase 3: LLM processing (requires scraped data + market data)
uv run python -m src.pipeline.orchestrator process
```

### Output

All data is saved to `data/` with date partitioning:

```
data/
├── raw/
│   ├── news/date=2025-01-05/news_raw_20250105_*.parquet
│   └── market/date=2025-01-05/market_snapshot_*.parquet
├── processed/
│   └── news/date=2025-01-05/processed_news_*.parquet
└── gates/
    └── date=2025-01-05/gate_checks_*.parquet
```

---

## Chain Prompting Details

### 4-Step Analysis with COT

Each news article goes through 4 sequential steps:

#### Step 1: Summarization
- **Input**: Full article text + title
- **Output**: 3-4 sentence summary + COT reasoning
- **Prompt**: Analyze actors, events, statements, economic context

#### Step 2: Topic Extraction
- **Input**: Summary + title
- **Output**: Topic categories + confidence + COT reasoning
- **Categories**: economy, politics, security, energy, international, monetary
- **Prompt**: Systematic sector analysis

#### Step 3: Impact Analysis
- **Input**: Summary + topics + market context (USD/COP, Brent oil, DXY, VIX)
- **Output**: Direction (POSITIVE/NEGATIVE/NEUTRAL) + mechanisms + confidence + COT
- **Prompt**: Analyze impact on exports, investment, fiscal stability, Central Bank policy

#### Step 4: Ranking (1-5)
- **Input**: Summary + topics + impact
- **Output**: Score (1-5) + category + justification + trader action + COT
- **Scale**:
  - 1 = Irrelevant (sports, entertainment)
  - 2 = Low (minor news)
  - 3 = Moderate (sector-specific)
  - 4 = High (major sectors/policy)
  - 5 = Critical (oil shock, Central Bank action)

---

## Gate Checks (Cost Optimization)

Gates filter articles BEFORE LLM processing to save ~70% of API costs:

| Gate | Check | Typical Pass Rate |
|------|-------|-------------------|
| 1. Content Quality | Min 200 chars, >80% Spanish, has title+content | ~90% |
| 2. Topic Relevance | ≥2 keyword matches from economy/politics/energy | ~50% |
| 3. Duplicate Detection | Hash + fuzzy title matching (>0.9 similarity) | ~80% |
| 4. Temporal Relevance | Max 48 hours old | ~95% |

**Overall**: ~30% of articles pass all gates → Significant cost savings

---

## Cost Analysis

### Estimated Costs

**Daily** (assuming 50 articles scraped, 15 pass gates):
- Input tokens: 15 × 10,000 = 150K tokens → $0.45
- Output tokens: 15 × 2,000 = 30K tokens → $0.45
- **Total: ~$0.90/day**

**Monthly**: ~$27

**Without Gate Checks**: ~$3.00/day (233% more expensive)

### Cost Tracking

Every run generates a cost report:

```json
{
  "date": "2025-01-05",
  "total_articles": 15,
  "total_tokens": 180000,
  "total_cost_usd": 0.90,
  "avg_cost_per_article": 0.06,
  "cost_breakdown": [...]
}
```

---

## Configuration

### Environment Variables

See `.env.example` for all options. Key variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
MAX_ARTICLES_PER_RUN=100
LOG_LEVEL=INFO
ENABLE_COST_ALERTS=true
DAILY_COST_THRESHOLD_USD=10.0
```

### Constants

Edit `src/config/constants.py` to customize:
- Min/max content length
- Keyword lists for topic relevance
- Market indicators to track
- Temperature and token limits

---

## Development

### Project Structure

```
src/
├── config/          # Settings, constants
├── models/          # Pydantic schemas, prompts, enums
├── scrapers/        # CNN Colombia, Yahoo Finance
├── gates/           # 4 gate check implementations
├── processors/      # LLM client, chain executor
├── storage/         # Parquet read/write
├── pipeline/        # Orchestrator, cost tracker
├── monitoring/      # Logging
└── utils/           # Date, hash, retry utilities
```

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/

# Integration tests (with mocks)
uv run pytest tests/integration/

# E2E tests (requires API key, costs money)
uv run pytest tests/e2e/ --runslow
```

### Adding New Features

1. **New Gate**: Extend `BaseGate` in `src/gates/`
2. **New Scraper**: Extend `BaseScraper` in `src/scrapers/`
3. **New Processing Step**: Modify `ChainExecutor` in `src/processors/`
4. **New Prompt**: Edit `src/models/prompts.py`

---

## GitHub Actions (CI/CD)

### Daily Pipeline

Runs automatically every day at 9 AM UTC:

```yaml
# .github/workflows/daily_pipeline.yml
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:     # Manual trigger
```

### Required Secrets

Add these in GitHub repository settings:

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `GCP_PROJECT_ID`: (Optional) For cloud storage
- `GCP_BUCKET_NAME`: (Optional) For cloud storage

---

## Troubleshooting

### Common Issues

**"No API key found"**
- Ensure `.env` file exists with `ANTHROPIC_API_KEY=...`
- Check that `.env` is not in `.gitignore` (but don't commit it!)

**"Failed to parse JSON response"**
- Claude sometimes wraps JSON in markdown. The code handles this.
- Check prompt format in `src/models/prompts.py`

**"No articles passed gates"**
- Check keyword list in `src/config/constants.py`
- Lower `MIN_KEYWORD_MATCHES` or adjust `MAX_ARTICLE_AGE_HOURS`

**High costs**
- Use `--max-articles 10` for testing
- Use `--mock-llm` flag to test without API calls
- Check gate pass rates (should be ~30%)

---

## Roadmap

- [ ] GCP Cloud Storage integration
- [ ] Streamlit dashboard for visualization
- [ ] BigQuery for SQL analysis
- [ ] LangGraph for more complex agentic workflows
- [ ] Correlation analysis with USD/COP historical data
- [ ] Alert system for critical news (score=5)
- [ ] Multi-source scraping (El Tiempo, Portafolio)
- [ ] Fine-tuned topic classifier (reduce gate checking costs)

---

## License

MIT License - See LICENSE file for details

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## Contact

For questions or issues, open a GitHub issue.
