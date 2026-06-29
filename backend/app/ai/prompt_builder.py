"""Build structured prompts for Kubernetes troubleshooting."""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are a Senior Kubernetes Site Reliability Engineer (SRE) performing incident triage.

Your job is to analyze collected cluster evidence and produce a precise, actionable diagnosis.
You must correlate evidence across pods, logs, events, deployments, and networking — never summarize a single source in isolation.

Rules:
- Be specific: name namespaces, pod names, deployments, and error messages from the evidence.
- Identify the most likely root cause, not every possible symptom.
- Suggest practical, beginner-friendly fixes with exact kubectl commands.
- Avoid vague advice like "check the logs" or "investigate further" without concrete next steps.
- If the cluster appears healthy, say so clearly and explain what you checked.
- Return ONLY valid JSON matching the schema below. No markdown, no extra text.

Required JSON schema:
{
  "root_cause": "One concise sentence stating the root cause",
  "explanation": "2-4 sentences correlating pod status, logs, events, deployments, and network evidence",
  "fix": "Clear step-by-step fix a junior engineer can follow",
  "kubectl_commands": ["kubectl command 1", "kubectl command 2"],
  "prevention_recommendation": "How to prevent this class of failure in the future",
  "confidence": 85,
  "confidence_reasons": ["Reason 1 tied to specific evidence", "Reason 2"]
}

Confidence scoring guide:
- 90-100: Multiple evidence sources agree (pod state + logs + events)
- 70-89: Strong signal from logs or events with supporting pod/deployment state
- 50-69: Partial evidence; root cause is likely but not fully confirmed
- Below 50: Insufficient or conflicting evidence"""


def build_messages(investigation: dict[str, Any]) -> list[dict[str, str]]:
    """
    Build OpenRouter chat messages from an investigation payload.

    Args:
        investigation: Output from the Kubernetes Investigation Layer.

    Returns:
        List of role/content message dicts for the chat completions API.
    """
    evidence = _format_evidence(investigation)

    user_prompt = f"""Analyze the following Kubernetes troubleshooting evidence and return your diagnosis as JSON.

=== POD STATUS ===
{evidence["pods"]}

=== LOGS ===
{evidence["logs"]}

=== EVENTS ===
{evidence["events"]}

=== DEPLOYMENT HEALTH ===
{evidence["deployments"]}

=== NETWORKING ===
{evidence["network"]}

Correlate all sections above. Return JSON only."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _format_evidence(investigation: dict[str, Any]) -> dict[str, str]:
    """Format each investigation section as readable JSON for the prompt."""
    sections = ("pods", "logs", "events", "deployments", "network")
    return {
        section: json.dumps(investigation.get(section, {}), indent=2)
        for section in sections
    }
