"""Analyze Kubernetes events for common failure patterns."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.kubernetes.kubectl_executor import run_kubectl_json

# Event reasons we care about during troubleshooting.
WATCHED_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
}


def analyze_events(context: str | None = None) -> dict[str, Any]:
    """
    Read cluster events and summarize findings for watched failure reasons.

    Returns grouped summaries with counts and recent examples.
    """
    result = run_kubectl_json(["get", "events", "-A", "--sort-by=.lastTimestamp"], context=context)
    if not result.success:
        return {
            "healthy": False,
            "total_events": 0,
            "findings": [],
            "error": result.error,
        }

    items = (result.data or {}).get("items", [])
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for event in items:
        reason = event.get("reason", "")
        if reason not in WATCHED_REASONS:
            continue

        involved = event.get("involvedObject", {})
        grouped[reason].append(
            {
                "namespace": involved.get("namespace", "default"),
                "resource": involved.get("kind", "Unknown"),
                "name": involved.get("name", "unknown"),
                "message": event.get("message", ""),
                "type": event.get("type", "Normal"),
                "count": str(event.get("count", 1)),
            }
        )

    findings = []
    for reason, events in grouped.items():
        findings.append(
            {
                "reason": reason,
                "count": len(events),
                "examples": events[-3:],
            }
        )

    findings.sort(key=lambda item: item["count"], reverse=True)

    return {
        "healthy": len(findings) == 0,
        "total_events": len(items),
        "watched_reasons_found": len(findings),
        "findings": findings,
    }
