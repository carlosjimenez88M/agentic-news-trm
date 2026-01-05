"""Anthropic Claude LLM client wrapper."""

import json
import logging
from typing import Optional, Dict, Any
from anthropic import Anthropic

from src.config.settings import settings
from src.config.constants import (
    ANTHROPIC_MODEL,
    MAX_TOKENS_PER_STEP,
    TEMPERATURE
)

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize LLM client.

        Args:
            api_key: Anthropic API key (default: from settings)
            model: Model to use (default: from constants)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or ANTHROPIC_MODEL
        self.client = Anthropic(api_key=self.api_key)

    def call(
        self,
        prompt: str,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS_PER_STEP,
        system_prompt: Optional[str] = None
    ) -> tuple[str, int, int]:
        """Call Claude API with a prompt.

        Args:
            prompt: User prompt
            temperature: Temperature for sampling (0.0-1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt

        Returns:
            Tuple of (response_text, input_tokens, output_tokens)

        Raises:
            Exception: If API call fails
        """
        try:
            logger.info(f"Calling Claude API (model: {self.model})")

            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Make API call
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }

            # Only add system if provided
            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)

            # Extract response text
            response_text = response.content[0].text

            # Get token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            logger.info(
                f"Claude API call successful. "
                f"Tokens: {input_tokens} in, {output_tokens} out"
            )

            return response_text, input_tokens, output_tokens

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def call_with_json_response(
        self,
        prompt: str,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS_PER_STEP,
        system_prompt: Optional[str] = None
    ) -> tuple[Dict[str, Any], int, int]:
        """Call Claude API and parse JSON response.

        Args:
            prompt: User prompt (should request JSON output)
            temperature: Temperature for sampling
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt

        Returns:
            Tuple of (parsed_json_dict, input_tokens, output_tokens)

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            Exception: If API call fails
        """
        response_text, input_tokens, output_tokens = self.call(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )

        # Try to parse JSON
        try:
            # Claude sometimes wraps JSON in markdown code blocks
            response_text = response_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```

            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```

            response_text = response_text.strip()

            # Parse JSON
            parsed_json = json.loads(response_text)

            return parsed_json, input_tokens, output_tokens

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            raise


class MockLLMClient:
    """Mock LLM client for testing (returns dummy responses)."""

    def __init__(self):
        """Initialize mock client."""
        logger.warning("Using MockLLMClient - responses will be dummy data")

    def call(
        self,
        prompt: str,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS_PER_STEP,
        system_prompt: Optional[str] = None
    ) -> tuple[str, int, int]:
        """Return mock response.

        Args:
            prompt: User prompt (ignored)
            temperature: Temperature (ignored)
            max_tokens: Max tokens (ignored)
            system_prompt: System prompt (ignored)

        Returns:
            Tuple of (mock_response, mock_input_tokens, mock_output_tokens)
        """
        mock_response = "Mock LLM response for testing"
        return mock_response, 100, 50

    def call_with_json_response(
        self,
        prompt: str,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS_PER_STEP,
        system_prompt: Optional[str] = None
    ) -> tuple[Dict[str, Any], int, int]:
        """Return mock JSON response.

        Args:
            prompt: User prompt (ignored)
            temperature: Temperature (ignored)
            max_tokens: Max tokens (ignored)
            system_prompt: System prompt (ignored)

        Returns:
            Tuple of (mock_json_dict, mock_input_tokens, mock_output_tokens)
        """
        mock_json = {
            "mock": True,
            "response": "Mock JSON response for testing"
        }
        return mock_json, 100, 50


def get_llm_client(mock: bool = False) -> LLMClient | MockLLMClient:
    """Factory function to get LLM client.

    Args:
        mock: Whether to use mock client

    Returns:
        LLMClient or MockLLMClient
    """
    if mock or settings.mock_llm:
        return MockLLMClient()
    return LLMClient()
