"""Google Gemini LLM client using HTTPX.

Exposes the same `chat_completion(messages) -> str` contract the rest of the
app relies on: it accepts OpenAI-style role/content messages and returns the
assistant's reply as a JSON-object string.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_TIMEOUT = 60.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0


class LLMClientError(Exception):
    """Raised when the Gemini API call fails after retries."""


def _build_url() -> str:
    if not settings.GEMINI_API_KEY:
        raise LLMClientError(
            "GEMINI_API_KEY is not configured. Add your Google AI Studio key to backend/.env"
        )
    return f"{GEMINI_BASE_URL}/{settings.GEMINI_MODEL}:generateContent"


def _build_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.GEMINI_API_KEY or "",
    }


def _to_gemini_request(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Translate OpenAI-style messages into a Gemini generateContent body.

    - `system` messages become a single `systemInstruction`.
    - `user`/`assistant` messages become `contents` with roles user/model.
    """
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []

    for message in messages:
        role = message.get("role")
        text = message.get("content", "")
        if role == "system":
            system_parts.append(text)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": text}]})

    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.1,
            # Ask Gemini to emit raw JSON, matching the OpenRouter json_object mode.
            "responseMimeType": "application/json",
        },
    }
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}

    return payload


def _extract_text(data: dict[str, Any], raw_text: str) -> str:
    candidates = data.get("candidates")
    if not candidates:
        feedback = data.get("promptFeedback")
        raise LLMClientError(
            f"Gemini returned no candidates (possibly blocked): {feedback or raw_text[:300]}"
        )

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", [])
    content = "".join(part.get("text", "") for part in parts).strip()
    if not content:
        finish = candidate.get("finishReason")
        raise LLMClientError(f"Gemini returned an empty response (finishReason={finish})")
    return content


async def chat_completion(messages: list[dict[str, str]]) -> str:
    """
    Send a chat completion request to Google Gemini with retries.

    Args:
        messages: OpenAI-style chat messages.

    Returns:
        The assistant message content string (expected to be JSON).

    Raises:
        LLMClientError: On missing API key or exhausted retries.
    """
    url = _build_url()
    headers = _build_headers()
    payload = _to_gemini_request(messages)
    last_error: str | None = None

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    "Gemini request attempt {}/{} model={}",
                    attempt,
                    MAX_RETRIES,
                    settings.GEMINI_MODEL,
                )
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 429:
                    last_error = "Rate limited by Gemini (429)"
                    logger.warning(last_error)
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue

                if response.status_code in (401, 403):
                    raise LLMClientError(
                        "Gemini rejected the API key (unauthorized). Verify GEMINI_API_KEY "
                        "in backend/.env — create one at https://aistudio.google.com/apikey"
                    )

                if response.status_code == 404:
                    raise LLMClientError(
                        f"Model '{settings.GEMINI_MODEL}' not found. Update GEMINI_MODEL in "
                        "backend/.env (e.g. gemini-2.0-flash or gemini-1.5-flash)."
                    )

                if response.status_code == 400:
                    # Gemini reports invalid keys / bad requests as 400 with a detail body.
                    raise LLMClientError(
                        f"Gemini rejected the request (400): {response.text[:300]}"
                    )

                if response.status_code >= 500:
                    last_error = f"Gemini server error ({response.status_code})"
                    logger.warning("{}: {}", last_error, response.text[:200])
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue

                if response.status_code != 200:
                    raise LLMClientError(
                        f"Gemini API error ({response.status_code}): {response.text[:300]}"
                    )

                content = _extract_text(response.json(), response.text)
                logger.info("Gemini response received successfully")
                return content

            except httpx.TimeoutException:
                last_error = f"Gemini request timed out after {DEFAULT_TIMEOUT}s"
                logger.warning("Attempt {}: {}", attempt, last_error)
            except httpx.RequestError as exc:
                last_error = f"Network error calling Gemini: {exc}"
                logger.warning("Attempt {}: {}", attempt, last_error)

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise LLMClientError(last_error or "Gemini request failed after retries")
