"""Chain executor for 4-step COT processing of news articles."""

import logging
from datetime import datetime
from typing import Optional

from src.processors.llm_client import LLMClient, get_llm_client
from src.models.schemas import (
    RawNews, MarketSnapshot, ProcessedNews,
    SummarizationOutput, TopicExtractionOutput,
    ImpactAnalysisOutput, RankingOutput
)
from src.models.enums import (
    ProcessingStage, TopicCategory, ImpactDirection,
    TimeHorizon, RankingCategory, TraderAction
)
from src.models.prompts import (
    STEP_1_SUMMARIZATION,
    STEP_2_TOPIC_EXTRACTION,
    STEP_3_IMPACT_ANALYSIS,
    STEP_4_RANKING
)

logger = logging.getLogger(__name__)


class ChainExecutor:
    """Executes 4-step chain prompting pipeline with COT."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize chain executor.

        Args:
            llm_client: LLM client to use (default: create new one)
        """
        self.llm_client = llm_client or get_llm_client()

    def execute_step_1(
        self,
        article: RawNews
    ) -> tuple[SummarizationOutput, int, int, int]:
        """Execute Step 1: Summarization.

        Args:
            article: Raw news article

        Returns:
            Tuple of (SummarizationOutput, input_tokens, output_tokens, processing_time_ms)
        """
        logger.info(f"[Step 1] Summarizing article {article.article_id}")

        start_time = datetime.now()

        # Format prompt
        prompt = STEP_1_SUMMARIZATION.format(
            title=article.title,
            content=article.content
        )

        # Call LLM
        response_json, input_tokens, output_tokens = self.llm_client.call_with_json_response(prompt)

        # Parse output
        summary_output = SummarizationOutput(
            summary=response_json.get("summary", ""),
            cot_reasoning=response_json.get("reasoning", "")
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(f"[Step 1] Completed in {processing_time_ms}ms")

        return summary_output, input_tokens, output_tokens, processing_time_ms

    def execute_step_2(
        self,
        article: RawNews,
        summary: str
    ) -> tuple[TopicExtractionOutput, int, int, int]:
        """Execute Step 2: Topic Extraction.

        Args:
            article: Raw news article
            summary: Summary from step 1

        Returns:
            Tuple of (TopicExtractionOutput, input_tokens, output_tokens, processing_time_ms)
        """
        logger.info(f"[Step 2] Extracting topics for article {article.article_id}")

        start_time = datetime.now()

        # Format prompt
        prompt = STEP_2_TOPIC_EXTRACTION.format(
            summary=summary,
            title=article.title
        )

        # Call LLM
        response_json, input_tokens, output_tokens = self.llm_client.call_with_json_response(prompt)

        # Parse topics (convert strings to TopicCategory enums)
        topic_strings = response_json.get("topics", [])
        topics = []
        for topic_str in topic_strings:
            try:
                topics.append(TopicCategory(topic_str))
            except ValueError:
                logger.warning(f"Invalid topic category: {topic_str}, skipping")

        # Create output
        topic_output = TopicExtractionOutput(
            topics=topics if topics else [TopicCategory.OTHER],
            cot_reasoning=response_json.get("reasoning", ""),
            confidence=response_json.get("confidence", 0.5)
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(f"[Step 2] Completed in {processing_time_ms}ms. Topics: {topics}")

        return topic_output, input_tokens, output_tokens, processing_time_ms

    def execute_step_3(
        self,
        article: RawNews,
        summary: str,
        topics: list[TopicCategory],
        market_context: MarketSnapshot
    ) -> tuple[ImpactAnalysisOutput, int, int, int]:
        """Execute Step 3: Impact Analysis.

        Args:
            article: Raw news article
            summary: Summary from step 1
            topics: Topics from step 2
            market_context: Current market snapshot

        Returns:
            Tuple of (ImpactAnalysisOutput, input_tokens, output_tokens, processing_time_ms)
        """
        logger.info(f"[Step 3] Analyzing impact for article {article.article_id}")

        start_time = datetime.now()

        # Format market context
        market_context_str = market_context.to_context_string()

        # Format prompt
        prompt = STEP_3_IMPACT_ANALYSIS.format(
            summary=summary,
            topics=", ".join([t.value for t in topics]),
            market_context=market_context_str
        )

        # Call LLM
        response_json, input_tokens, output_tokens = self.llm_client.call_with_json_response(prompt)

        # Parse output
        impact_output = ImpactAnalysisOutput(
            direction=ImpactDirection(response_json.get("direction", "NEUTRAL")),
            mechanisms=response_json.get("mechanisms", []),
            confidence=response_json.get("confidence", 0.5),
            time_horizon=TimeHorizon(response_json.get("time_horizon", "medium-term")),
            cot_reasoning=response_json.get("reasoning", "")
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(
            f"[Step 3] Completed in {processing_time_ms}ms. "
            f"Direction: {impact_output.direction.value}"
        )

        return impact_output, input_tokens, output_tokens, processing_time_ms

    def execute_step_4(
        self,
        article: RawNews,
        summary: str,
        topics: list[TopicCategory],
        impact: ImpactAnalysisOutput
    ) -> tuple[RankingOutput, int, int, int]:
        """Execute Step 4: Ranking.

        Args:
            article: Raw news article
            summary: Summary from step 1
            topics: Topics from step 2
            impact: Impact analysis from step 3

        Returns:
            Tuple of (RankingOutput, input_tokens, output_tokens, processing_time_ms)
        """
        logger.info(f"[Step 4] Ranking article {article.article_id}")

        start_time = datetime.now()

        # Format impact as string
        impact_str = (
            f"Direction: {impact.direction.value}, "
            f"Mechanisms: {', '.join(impact.mechanisms)}, "
            f"Confidence: {impact.confidence:.2f}, "
            f"Time horizon: {impact.time_horizon.value}"
        )

        # Format prompt
        prompt = STEP_4_RANKING.format(
            summary=summary,
            topics=", ".join([t.value for t in topics]),
            impact=impact_str
        )

        # Call LLM
        response_json, input_tokens, output_tokens = self.llm_client.call_with_json_response(prompt)

        # Parse output
        score = response_json.get("score", 3)
        category_str = response_json.get("category", "Moderate")

        # Map score to category if category is invalid
        score_to_category = {
            1: RankingCategory.IRRELEVANT,
            2: RankingCategory.LOW,
            3: RankingCategory.MODERATE,
            4: RankingCategory.HIGH,
            5: RankingCategory.CRITICAL
        }
        category = score_to_category.get(score, RankingCategory.MODERATE)

        # Map score to trader action
        if score <= 2:
            trader_action = TraderAction.MONITOR
        elif score <= 4:
            trader_action = TraderAction.ALERT
        else:
            trader_action = TraderAction.URGENT

        ranking_output = RankingOutput(
            score=score,
            category=category,
            justification=response_json.get("justification", ""),
            trader_action=trader_action,
            cot_reasoning=response_json.get("reasoning", "")
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(
            f"[Step 4] Completed in {processing_time_ms}ms. "
            f"Score: {score}, Category: {category.value}"
        )

        return ranking_output, input_tokens, output_tokens, processing_time_ms

    def execute_full_chain(
        self,
        article: RawNews,
        market_context: MarketSnapshot
    ) -> ProcessedNews:
        """Execute the full 4-step chain on an article.

        Args:
            article: Raw news article
            market_context: Current market snapshot

        Returns:
            ProcessedNews with all outputs
        """
        logger.info(f"Starting full chain execution for article {article.article_id}")

        total_input_tokens = 0
        total_output_tokens = 0
        total_processing_time_ms = 0

        try:
            # Step 1: Summarization
            summary_output, in_tok, out_tok, proc_time = self.execute_step_1(article)
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_processing_time_ms += proc_time

            # Step 2: Topic Extraction
            topic_output, in_tok, out_tok, proc_time = self.execute_step_2(
                article, summary_output.summary
            )
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_processing_time_ms += proc_time

            # Step 3: Impact Analysis
            impact_output, in_tok, out_tok, proc_time = self.execute_step_3(
                article, summary_output.summary, topic_output.topics, market_context
            )
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_processing_time_ms += proc_time

            # Step 4: Ranking
            ranking_output, in_tok, out_tok, proc_time = self.execute_step_4(
                article, summary_output.summary, topic_output.topics, impact_output
            )
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_processing_time_ms += proc_time

            # Create ProcessedNews object
            processed = ProcessedNews(
                article_id=article.article_id,
                processing_stage=ProcessingStage.RANKING,
                chain_step=4,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                processing_time_ms=total_processing_time_ms,
                processed_at=datetime.now(),
                # Step 1 outputs
                summary=summary_output.summary,
                summary_cot=summary_output.cot_reasoning,
                # Step 2 outputs
                topics=topic_output.topics,
                topics_cot=topic_output.cot_reasoning,
                topics_confidence=topic_output.confidence,
                # Step 3 outputs
                impact_direction=impact_output.direction,
                impact_mechanisms=impact_output.mechanisms,
                impact_confidence=impact_output.confidence,
                impact_time_horizon=impact_output.time_horizon,
                impact_cot=impact_output.cot_reasoning,
                # Step 4 outputs
                ranking_score=ranking_output.score,
                ranking_category=ranking_output.category,
                ranking_justification=ranking_output.justification,
                ranking_trader_action=ranking_output.trader_action,
                ranking_cot=ranking_output.cot_reasoning
            )

            logger.info(
                f"Full chain completed for article {article.article_id}. "
                f"Total tokens: {total_input_tokens + total_output_tokens}, "
                f"Total time: {total_processing_time_ms}ms, "
                f"Cost: ${processed.cost_usd:.4f}"
            )

            return processed

        except Exception as e:
            logger.error(f"Error executing chain for article {article.article_id}: {e}")
            raise
