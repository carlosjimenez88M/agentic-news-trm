"""Daily analysis: identify and analyze the most important news of the day."""

import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from src.models.schemas import ProcessedNews
from src.processors.llm_client import LLMClient, get_llm_client
from src.storage.local_parquet import ParquetStorage
from src.config.settings import settings

logger = logging.getLogger(__name__)


DAILY_ANALYSIS_PROMPT = """Eres un analista económico senior especializado en el mercado de divisas colombiano.

Se te presentan todas las noticias del día que han sido procesadas y rankeadas por su impacto en el tipo de cambio USD/COP.

<top_news>
{top_news_details}
</top_news>

<all_news_summary>
Total de noticias analizadas hoy: {total_news}
Distribución de rankings:
- Critical (5): {count_5} noticias
- High (4): {count_4} noticias
- Moderate (3): {count_3} noticias
- Low (2): {count_2} noticias
- Irrelevant (1): {count_1} noticias
</all_news_summary>

Tu tarea es analizar el contexto completo del día y explicar:

1. **Noticia más importante**: ¿Cuál es la noticia MÁS IMPORTANTE del día y por qué?
   - Si hay múltiples noticias con score 5, elige la de mayor impacto potencial
   - Si no hay noticias con score 5, elige la de mayor score

2. **Contexto del día**: ¿Qué nos dice el conjunto de noticias sobre la situación económica/política de Colombia hoy?

3. **Implicaciones para USD/COP**: Considerando TODAS las noticias del día, ¿cuál es la dirección probable del tipo de cambio en los próximos días?

4. **Recomendación para traders**: Basado en el análisis completo, ¿qué deben vigilar los traders de USD/COP?

Piensa paso a paso y proporciona un análisis profundo y fundamentado.

Responde en JSON con este formato:
{{
  "most_important_news": {{
    "article_id": "el ID de la noticia más importante",
    "title": "título de la noticia",
    "reasoning": "explicación detallada de por qué es la más importante (3-4 párrafos)"
  }},
  "daily_context": "análisis del contexto general del día (2-3 párrafos)",
  "usd_cop_outlook": {{
    "direction": "STRENGTHENING o WEAKENING o NEUTRAL",
    "confidence": "HIGH o MEDIUM o LOW",
    "explanation": "explicación de la dirección esperada (2 párrafos)"
  }},
  "trader_recommendations": [
    "recomendación 1",
    "recomendación 2",
    "recomendación 3"
  ]
}}"""


class DailyAnalyzer:
    """Analyzer for identifying and analyzing the most important news of the day."""

    def __init__(self, llm_client: LLMClient = None):
        """Initialize daily analyzer.

        Args:
            llm_client: LLM client to use (default: create new one)
        """
        self.llm_client = llm_client or get_llm_client()
        self.storage = ParquetStorage(settings.raw_data_dir)

    def load_daily_news(self, date: datetime = None) -> List[ProcessedNews]:
        """Load all processed news for a given date.

        Args:
            date: Date to load (default: today)

        Returns:
            List of ProcessedNews objects
        """
        # Note: This is a simplified version. In production, we'd read from Parquet
        # For now, we'll work with a list passed to the analyze method
        logger.info(f"Loading processed news for date: {date or datetime.now().date()}")
        return []

    def get_ranking_distribution(self, articles: List[ProcessedNews]) -> Dict[int, int]:
        """Get distribution of ranking scores.

        Args:
            articles: List of processed articles

        Returns:
            Dict mapping score to count
        """
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for article in articles:
            if article.ranking_score:
                distribution[article.ranking_score] = distribution.get(article.ranking_score, 0) + 1
        return distribution

    def get_top_news_details(self, articles: List[ProcessedNews], limit: int = 5) -> str:
        """Format top news for prompt.

        Args:
            articles: List of processed articles
            limit: Maximum number of top articles to include

        Returns:
            Formatted string with top news details
        """
        # Sort by ranking score (descending)
        sorted_articles = sorted(
            articles,
            key=lambda x: (x.ranking_score or 0, x.impact_confidence or 0),
            reverse=True
        )[:limit]

        details = []
        for i, article in enumerate(sorted_articles, 1):
            detail = f"""
Noticia #{i}:
- ID: {article.article_id}
- Título: {article.summary[:200] if article.summary else "N/A"}...
- Ranking: {article.ranking_score}/5 ({article.ranking_category.value if article.ranking_category else "N/A"})
- Topics: {", ".join([t.value for t in article.topics]) if article.topics else "N/A"}
- Impacto USD/COP: {article.impact_direction.value if article.impact_direction else "N/A"}
- Confianza: {f"{article.impact_confidence:.2f}" if article.impact_confidence is not None else "0.00"}
- Justificación: {article.ranking_justification if article.ranking_justification else "N/A"}
- Resumen: {article.summary if article.summary else "N/A"}
"""
            details.append(detail.strip())

        return "\n\n".join(details)

    def analyze_daily_news(
        self,
        articles: List[ProcessedNews],
        date: datetime = None
    ) -> Dict[str, Any]:
        """Analyze all daily news and identify the most important one.

        Args:
            articles: List of processed articles
            date: Date of analysis (default: today)

        Returns:
            Dict with analysis results
        """
        if not articles:
            logger.warning("No articles to analyze")
            return {
                "error": "No articles provided",
                "date": (date or datetime.now()).strftime("%Y-%m-%d")
            }

        logger.info(f"Analyzing {len(articles)} articles for daily summary")

        # Get ranking distribution
        distribution = self.get_ranking_distribution(articles)

        # Format top news details
        top_news_details = self.get_top_news_details(articles, limit=5)

        # Format prompt
        prompt = DAILY_ANALYSIS_PROMPT.format(
            top_news_details=top_news_details,
            total_news=len(articles),
            count_5=distribution[5],
            count_4=distribution[4],
            count_3=distribution[3],
            count_2=distribution[2],
            count_1=distribution[1]
        )

        # Call LLM
        try:
            response_json, input_tokens, output_tokens = self.llm_client.call_with_json_response(
                prompt,
                max_tokens=3000  # Longer response for comprehensive analysis
            )

            # Add metadata
            response_json["date"] = (date or datetime.now()).strftime("%Y-%m-%d")
            response_json["total_articles_analyzed"] = len(articles)
            response_json["ranking_distribution"] = distribution
            response_json["tokens_used"] = {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }

            logger.info("Daily analysis completed successfully")

            return response_json

        except Exception as e:
            logger.error(f"Failed to generate daily analysis: {e}")
            return {
                "error": str(e),
                "date": (date or datetime.now()).strftime("%Y-%m-%d")
            }

    def format_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """Format analysis as a readable report.

        Args:
            analysis: Analysis results from analyze_daily_news

        Returns:
            Formatted report string
        """
        if "error" in analysis:
            return f"❌ Error en el análisis: {analysis['error']}"

        report = []
        report.append("=" * 80)
        report.append(f"📊 ANÁLISIS DIARIO - {analysis['date']}")
        report.append("=" * 80)
        report.append("")

        # Most important news
        most_important = analysis.get("most_important_news", {})
        report.append("🔥 NOTICIA MÁS IMPORTANTE DEL DÍA")
        report.append("-" * 80)
        report.append(f"Título: {most_important.get('title', 'N/A')}")
        report.append(f"ID: {most_important.get('article_id', 'N/A')}")
        report.append("")
        report.append("¿Por qué es la más importante?")
        report.append(most_important.get('reasoning', 'N/A'))
        report.append("")

        # Daily context
        report.append("📰 CONTEXTO DEL DÍA")
        report.append("-" * 80)
        report.append(analysis.get('daily_context', 'N/A'))
        report.append("")

        # USD/COP outlook
        outlook = analysis.get('usd_cop_outlook', {})
        report.append("💱 PERSPECTIVA USD/COP")
        report.append("-" * 80)
        report.append(f"Dirección: {outlook.get('direction', 'N/A')}")
        report.append(f"Confianza: {outlook.get('confidence', 'N/A')}")
        report.append("")
        report.append(outlook.get('explanation', 'N/A'))
        report.append("")

        # Trader recommendations
        recommendations = analysis.get('trader_recommendations', [])
        report.append("💡 RECOMENDACIONES PARA TRADERS")
        report.append("-" * 80)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
        report.append("")

        # Stats
        report.append("📈 ESTADÍSTICAS")
        report.append("-" * 80)
        report.append(f"Total noticias analizadas: {analysis.get('total_articles_analyzed', 0)}")

        distribution = analysis.get('ranking_distribution', {})
        report.append("Distribución de rankings:")
        report.append(f"  • Critical (5): {distribution.get(5, 0)} noticias")
        report.append(f"  • High (4): {distribution.get(4, 0)} noticias")
        report.append(f"  • Moderate (3): {distribution.get(3, 0)} noticias")
        report.append(f"  • Low (2): {distribution.get(2, 0)} noticias")
        report.append(f"  • Irrelevant (1): {distribution.get(1, 0)} noticias")
        report.append("")

        tokens = analysis.get('tokens_used', {})
        report.append(f"Tokens usados: {tokens.get('total', 0):,} (input: {tokens.get('input', 0):,}, output: {tokens.get('output', 0):,})")

        report.append("=" * 80)

        return "\n".join(report)


def analyze_daily_news(articles: List[ProcessedNews], date: datetime = None) -> Dict[str, Any]:
    """Helper function to analyze daily news.

    Args:
        articles: List of processed articles
        date: Date of analysis (default: today)

    Returns:
        Analysis results dict
    """
    analyzer = DailyAnalyzer()
    return analyzer.analyze_daily_news(articles, date)


def generate_daily_report(articles: List[ProcessedNews], date: datetime = None) -> str:
    """Helper function to generate formatted daily report.

    Args:
        articles: List of processed articles
        date: Date of analysis (default: today)

    Returns:
        Formatted report string
    """
    analyzer = DailyAnalyzer()
    analysis = analyzer.analyze_daily_news(articles, date)
    return analyzer.format_analysis_report(analysis)
