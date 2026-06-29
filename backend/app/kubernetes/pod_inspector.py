"""Inspect pod health across the cluster."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.kubernetes.kubectl_executor import run_kubectl_json

# Container waiting reasons that indicate a problem.
PROBLEMATIC_WAITING_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerError",
    "InvalidImageName",
    "Error",
}

# How long a pod may stay in ContainerCreating before we flag it as stuck.
STUCK_CONTAINER_CREATING_MINUTES = 5


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pod_age_minutes(pod: dict[str, Any]) -> float | None:
    created = _parse_timestamp(pod.get("metadata", {}).get("creationTimestamp"))
    if not created:
        return None
    return (datetime.now(timezone.utc) - created).total_seconds() / 60


def _collect_container_issues(container_statuses: list[dict[str, Any]]) -> list[str]:
    """Extract problem reasons from container status objects."""
    issues: list[str] = []

    for status in container_statuses or []:
        state = status.get("state", {})
        waiting = state.get("waiting", {})
        reason = waiting.get("reason", "")

        if reason in PROBLEMATIC_WAITING_REASONS:
            issues.append(reason)

        terminated = state.get("terminated", {})
        if terminated.get("reason") == "OOMKilled":
            issues.append("OOMKilled")

        last_terminated = status.get("lastState", {}).get("terminated", {})
        if last_terminated.get("reason") == "OOMKilled" and "OOMKilled" not in issues:
            issues.append("OOMKilled")

        if reason == "ContainerCreating":
            issues.append("ContainerCreating")

    return issues


def inspect_pods(context: str | None = None) -> dict[str, Any]:
    """
    Get pod status and detect unhealthy pods across all namespaces.

    Returns structured JSON with healthy flag and problematic pod list.
    """
    result = run_kubectl_json(["get", "pods", "-A"], context=context)
    if not result.success:
        return {
            "healthy": False,
            "total_pods": 0,
            "problematic_pods": [],
            "error": result.error,
        }

    items = (result.data or {}).get("items", [])
    problematic_pods: list[dict[str, str]] = []

    for pod in items:
        metadata = pod.get("metadata", {})
        status = pod.get("status", {})
        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        phase = status.get("phase", "Unknown")

        container_statuses = status.get("containerStatuses") or status.get("initContainerStatuses") or []
        issues = _collect_container_issues(container_statuses)

        # Pending pods are often scheduling or resource issues.
        if phase == "Pending" and "Pending" not in issues:
            issues.append("Pending")

        # Flag ContainerCreating as stuck when it persists too long.
        age_minutes = _pod_age_minutes(pod)
        if "ContainerCreating" in issues and age_minutes is not None:
            if age_minutes >= STUCK_CONTAINER_CREATING_MINUTES:
                issues = [i if i != "ContainerCreating" else "ContainerCreating (stuck)" for i in issues]
            else:
                issues = [i for i in issues if i != "ContainerCreating"]

        if phase == "Failed" and "Error" not in issues:
            issues.append("Error")

        for issue in dict.fromkeys(issues):
            problematic_pods.append(
                {
                    "name": name,
                    "namespace": namespace,
                    "status": issue,
                    "phase": phase,
                }
            )

    return {
        "healthy": len(problematic_pods) == 0,
        "total_pods": len(items),
        "problematic_pods": problematic_pods,
    }
