"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import logging
from dataclasses import dataclass

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client with OpenAI implementation."""

    # Pricing per 1M tokens for gpt-4o-mini (as of 2024)
    PRICING = {
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    }

    def __init__(self, model: str | None = None, temperature: float = 0.0):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_model
        self.temperature = temperature
        self.timeout = settings.timeout_seconds

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with retry logic and cost tracking."""
        try:
            logger.info(f"LLM call: model={self.model}, temp={self.temperature}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                timeout=self.timeout,
            )

            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else None
            output_tokens = response.usage.completion_tokens if response.usage else None

            # Calculate cost
            cost_usd = None
            if input_tokens and output_tokens and self.model in self.PRICING:
                pricing = self.PRICING[self.model]
                cost_usd = (
                    input_tokens * pricing["input"] / 1_000_000
                    + output_tokens * pricing["output"] / 1_000_000
                )

            logger.info(
                f"LLM response: tokens={input_tokens}/{output_tokens}, "
                f"cost=${cost_usd:.4f}" if cost_usd else "cost=unknown"
            )

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise AgentExecutionError(f"LLM completion failed: {e}") from e
