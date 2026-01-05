"""Settings configuration using Pydantic."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys
    anthropic_api_key: str
    openai_api_key: Optional[str] = None  # Optional, not used currently
    google_api_key: Optional[str] = None  # Optional, not used currently

    # GCP Configuration
    gcp_project_id: Optional[str] = None
    gcp_bucket_name: Optional[str] = None
    gcp_credentials_path: Optional[str] = None

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    aggregated_data_dir: Path = data_dir / "aggregated"
    gates_data_dir: Path = data_dir / "gates"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    # Pipeline Configuration
    max_articles_per_run: int = 100
    scrape_timeout_seconds: int = 30
    enable_gcs_upload: bool = False  # Set to True to enable GCS uploads

    # Monitoring
    enable_cost_alerts: bool = True
    daily_cost_threshold_usd: float = 10.0
    alert_email: Optional[str] = None

    # Testing
    mock_llm: bool = False  # Set to True to use mock LLM for testing
    test_mode: bool = False  # Set to True to run in test mode

    def __init__(self, **kwargs):
        """Initialize settings and create data directories."""
        super().__init__(**kwargs)
        self._create_directories()

    def _create_directories(self):
        """Create necessary data directories if they don't exist."""
        for directory in [
            self.data_dir,
            self.raw_data_dir,
            self.raw_data_dir / "news",
            self.raw_data_dir / "market",
            self.processed_data_dir,
            self.processed_data_dir / "news",
            self.aggregated_data_dir,
            self.gates_data_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
