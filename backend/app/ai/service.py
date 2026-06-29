"""AI Kubernetes Agent — orchestrates LLM reasoning over investigation evidence."""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.ai.confidence_engine import compute_confidence
from app.ai.fix_recommendation_engine import build_fix_recommendation
from app.ai.llm_client import LLMClientError
from app.ai.root_cause_analyzer import analyze_root_cause


async def diagnose(investigation: dict[str, Any]) -> dict[str, Any]:
    """
    Run the full AI reasoning pipeline on investigation evidence.

    Flow:
        1. Send evidence to LLM for root cause analysis
        2. Build actionable fix recommendations
        3. Compute confidence score from correlated evidence

    Returns:
        Structured diagnosis dict ready for the API response.
    """
    logger.info("Starting AI diagnosis")

    try:
        analysis = await analyze_root_cause(investigation)
    except LLMClientError as exc:
        logger.error("AI diagnosis failed: {}", exc)
        error_msg = str(exc)
        fix_hint = (
            "Gemini is rate limited — wait a moment and retry, or raise your quota."
            if "rate limited" in error_msg.lower()
            else "Configure GEMINI_API_KEY in backend/.env and retry."
        )
        return {
            "root_cause": "AI analysis unavailable",
            "explanation": error_msg,
            "fix": fix_hint,
            "kubectl_command": "kubectl get pods -A",
            "kubectl_commands": ["kubectl get pods -A"],
            "prevention_recommendation": "Ensure a valid GEMINI_API_KEY is configured in backend/.env.",
            "confidence": 0,
            "confidence_reasons": ["LLM call failed — no AI reasoning performed"],
            "error": error_msg,
        }

    fix = build_fix_recommendation(analysis, investigation)
    confidence = compute_confidence(analysis, investigation)

    diagnosis = {
        "root_cause": analysis.get("root_cause", ""),
        "explanation": analysis.get("explanation", ""),
        "fix": fix["fix"],
        "kubectl_command": fix["kubectl_command"],
        "kubectl_commands": fix["kubectl_commands"],
        "prevention_recommendation": fix["prevention_recommendation"],
        "confidence": confidence["confidence"],
        "confidence_reasons": confidence["confidence_reasons"],
    }

    logger.info(
        "AI diagnosis complete — root_cause='{}' confidence={}%",
        diagnosis["root_cause"][:80],
        diagnosis["confidence"],
    )
    return diagnosis
