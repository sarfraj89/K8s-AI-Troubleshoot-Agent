"""Compute confidence scores by correlating evidence with the AI diagnosis."""

from __future__ import annotations

from typing import Any


def _evidence_signals(investigation: dict[str, Any]) -> list[str]:
    """Collect concrete evidence signals present in the investigation."""
    signals: list[str] = []

    pods = investigation.get("pods", {})
    problematic = pods.get("problematic_pods", [])
    if problematic:
        for pod in problematic[:3]:
            signals.append(
                f"Pod {pod.get('namespace')}/{pod.get('name')} is {pod.get('status')}"
            )

    logs = investigation.get("logs", {})
    entries = logs.get("entries", {})
    if entries:
        signals.append(f"Logs collected for {len(entries)} problematic pod(s)")

    events = investigation.get("events", {})
    findings = events.get("findings", [])
    for finding in findings[:3]:
        signals.append(
            f"Event {finding.get('reason')} occurred {finding.get('count')} time(s)"
        )

    deployments = investigation.get("deployments", {})
    unhealthy = deployments.get("unhealthy_deployments", [])
    for dep in unhealthy[:2]:
        issues = dep.get("issues", [])
        if issues:
            signals.append(
                f"Deployment {dep.get('namespace')}/{dep.get('name')}: {issues[0]}"
            )

    network = investigation.get("network", {})
    issues = network.get("issues", [])
    for issue in issues[:2]:
        signals.append(
            f"Network issue on {issue.get('namespace')}/{issue.get('service')}: {issue.get('issue')}"
        )

    if pods.get("healthy") and not signals:
        signals.append("All checked pods, deployments, and services appear healthy")

    return signals


def _evidence_score(investigation: dict[str, Any]) -> int:
    """Score 0-100 based on how much corroborating evidence exists."""
    score = 0

    problematic = investigation.get("pods", {}).get("problematic_pods", [])
    log_entries = investigation.get("logs", {}).get("entries", {})
    event_findings = investigation.get("events", {}).get("findings", [])
    unhealthy_deps = investigation.get("deployments", {}).get("unhealthy_deployments", [])
    network_issues = investigation.get("network", {}).get("issues", [])

    if problematic:
        score += 25
    if log_entries:
        score += 30
    if event_findings:
        score += 20
    if unhealthy_deps:
        score += 15
    if network_issues:
        score += 10

    # Healthy cluster with no issues — high confidence in "no problems" diagnosis.
    if not any([problematic, log_entries, event_findings, unhealthy_deps, network_issues]):
        if investigation.get("pods", {}).get("healthy"):
            score = 90

    return min(score, 100)


def _text_overlap(root_cause: str, investigation: dict[str, Any]) -> bool:
    """Check if root cause text references evidence keywords from logs."""
    root_lower = root_cause.lower()
    for entry in investigation.get("logs", {}).get("entries", {}).values():
        for line in entry.get("lines", []):
            # Match significant words (4+ chars) from log lines in root cause.
            words = [w.lower() for w in line.split() if len(w) >= 4]
            if any(word in root_lower for word in words[:5]):
                return True
    return False


def compute_confidence(
    analysis: dict[str, Any],
    investigation: dict[str, Any],
) -> dict[str, Any]:
    """
    Blend LLM confidence with rule-based evidence correlation.

    Returns final confidence score (0-100) and human-readable reasons.
    """
    llm_confidence = analysis.get("confidence", 50)
    try:
        llm_confidence = int(llm_confidence)
    except (TypeError, ValueError):
        llm_confidence = 50

    llm_confidence = max(0, min(llm_confidence, 100))
    evidence = _evidence_score(investigation)
    evidence_signals = _evidence_signals(investigation)

    # Weighted blend: evidence correlation matters as much as LLM self-assessment.
    final_score = round((llm_confidence * 0.5) + (evidence * 0.5))

    reasons: list[str] = list(analysis.get("confidence_reasons") or [])

    if evidence_signals:
        reasons.append(f"Evidence collected: {'; '.join(evidence_signals[:3])}")

    if _text_overlap(analysis.get("root_cause", ""), investigation):
        final_score = min(100, final_score + 5)
        reasons.append("Root cause aligns with log error messages")

    if len(evidence_signals) >= 3:
        final_score = min(100, final_score + 5)
        reasons.append("Multiple independent evidence sources corroborate the diagnosis")

    final_score = max(0, min(final_score, 100))

    return {
        "confidence": final_score,
        "confidence_reasons": reasons[:6],
    }
