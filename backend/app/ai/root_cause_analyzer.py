"""Parse LLM output and extract root cause analysis."""

from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger

from app.ai.llm_client import LLMClientError, chat_completion
from app.ai.prompt_builder import build_messages


def _strip_json_fences(raw: str) -> str:
    """Remove markdown code fences if the model wrapped JSON in them."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_llm_response(raw: str) -> dict[str, Any]:
    """Parse the LLM JSON response into a dict."""
    cleaned = _strip_json_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM JSON: {}", exc)
        raise LLMClientError(f"LLM returned invalid JSON: {exc}") from exc

    required_fields = ("root_cause", "explanation", "fix")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise LLMClientError(f"LLM response missing required fields: {', '.join(missing)}")

    return data


async def analyze_root_cause(investigation: dict[str, Any]) -> dict[str, Any]:
    """
    Send investigation evidence to the LLM and extract root cause analysis.

    Args:
        investigation: Full payload from the Kubernetes Investigation Layer.

    Returns:
        Parsed LLM analysis dict with root_cause, explanation, fix, etc.
    """
    messages = build_messages(investigation)
    raw_response = await chat_completion(messages)
    analysis = _parse_llm_response(raw_response)

    logger.info("Root cause identified: {}", analysis.get("root_cause", "unknown"))
    return analysis
