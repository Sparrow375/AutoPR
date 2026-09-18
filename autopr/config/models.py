"""
AutoPR Model Layer — Unified LLM Client

Wraps Google GenAI (Gemini 2.5 Flash / Pro) and optional local Ollama models.
Provides structured output extraction, retry handling, and fallback capabilities.
"""

from __future__ import annotations

import logging
import re
from typing import Any, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from autopr.config.settings import get_settings

logger = logging.getLogger("autopr.models")

T = TypeVar("T", bound=BaseModel)


class ModelClient:
    """Unified client for invoking Gemini models and optional Ollama fallbacks."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.genai_client = (
            genai.Client(api_key=self.settings.gemini_api_key)
            if self.settings.gemini_api_key
            else None
        )

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
        temperature: float = 0.2,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generate response from Gemini or fallback to local LLM.

        Args:
            prompt: User prompt.
            system_instruction: System guidelines.
            model: Specific model name (e.g. 'gemini-2.5-flash', 'gemini-2.5-pro').
            temperature: Sampling temperature (0.0 to 1.0).
            response_schema: Optional Pydantic model class for structured JSON output.

        Returns:
            String response or parsed Pydantic model instance.
        """
        chosen_model = model or self.settings.default_model
        candidates = [chosen_model]
        for fallback in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]:
            if fallback not in candidates:
                candidates.append(fallback)

        if self.genai_client:
            for model_name in candidates:
                try:
                    config_kwargs: dict[str, Any] = {
                        "temperature": temperature,
                    }
                    if system_instruction:
                        config_kwargs["system_instruction"] = system_instruction

                    if response_schema:
                        config_kwargs["response_mime_type"] = "application/json"
                        config_kwargs["response_schema"] = response_schema

                    config = types.GenerateContentConfig(**config_kwargs)

                    response = self.genai_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )

                    text = response.text or ""

                    if response_schema:
                        try:
                            return response_schema.model_validate_json(text)
                        except Exception:
                            json_match = re.search(r"\{.*\}", text, re.DOTALL)
                            if json_match:
                                return response_schema.model_validate_json(json_match.group(0))
                            raise

                    return text

                except Exception as e:
                    logger.warning("Gemini model %s failed: %s, trying next candidate...", model_name, e)
                    continue

        # Fallback: Try local Ollama if installed and available
        try:
            import httpx

            ollama_url = f"{self.settings.ollama_base_url}/api/generate"
            full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
            res = httpx.post(
                ollama_url,
                json={"model": self.settings.ollama_model, "prompt": full_prompt, "stream": False},
                timeout=30.0,
            )
            if res.status_code == 200:
                text = res.json().get("response", "")
                if response_schema:
                    json_match = re.search(r"\{.*\}", text, re.DOTALL)
                    if json_match:
                        return response_schema.model_validate_json(json_match.group(0))
                return text
        except Exception:
            pass

        # If all else fails and structured schema requested, return empty mock instance
        if response_schema:
            logger.error("All model invocations failed. Generating fallback structured instance.")
            return response_schema.model_construct()

        return "Model invocation unavailable. Please check API configuration."


_GLOBAL_MODEL_CLIENT: ModelClient | None = None


def get_model_client() -> ModelClient:
    """Get or initialize singleton ModelClient."""
    global _GLOBAL_MODEL_CLIENT
    if _GLOBAL_MODEL_CLIENT is None:
        _GLOBAL_MODEL_CLIENT = ModelClient()
    return _GLOBAL_MODEL_CLIENT
