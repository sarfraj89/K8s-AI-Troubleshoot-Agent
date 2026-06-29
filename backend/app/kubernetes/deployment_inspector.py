"""Inspect deployments for replica and rollout issues."""

from __future__ import annotations

from typing import Any

from app.kubernetes.kubectl_executor import run_kubectl_json


def _deployment_issues(deployment: dict[str, Any]) -> list[str]:
    """Derive human-readable issues from a deployment object."""
    metadata = deployment.get("metadata", {})
    spec = deployment.get("spec", {})
    status = deployment.get("status", {})

    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    desired = spec.get("replicas", 1)
    available = status.get("availableReplicas", 0)
    unavailable = status.get("unavailableReplicas", 0)
    ready = status.get("readyReplicas", 0)
    updated = status.get("updatedReplicas", 0)

    issues: list[str] = []

    if available < desired:
        issues.append(f"Only {available}/{desired} replicas available")

    if unavailable > 0:
        issues.append(f"{unavailable} unavailable replica(s)")

    if ready < desired:
        issues.append(f"Only {ready}/{desired} replicas ready")

    if updated < desired:
        issues.append(f"Rollout in progress: {updated}/{desired} updated")

    for condition in status.get("conditions", []):
        condition_type = condition.get("type", "")
        condition_status = condition.get("status", "")
        message = condition.get("message", "")

        if condition_type == "Available" and condition_status != "True":
            issues.append(f"Not available: {message or 'condition False'}")
        if condition_type == "Progressing" and condition_status == "False":
            issues.append(f"Rollout failed: {message or 'Progressing=False'}")
        if condition_type == "ReplicaFailure" and condition_status == "True":
            issues.append(f"Replica failure: {message or 'ReplicaFailure detected'}")

    return issues


def inspect_deployments(context: str | None = None) -> dict[str, Any]:
    """
    Inspect all deployments and detect unhealthy ones.

    Checks available/unavailable replicas, rollout state, and conditions.
    """
    result = run_kubectl_json(["get", "deployments", "-A"], context=context)
    if not result.success:
        return {
            "healthy": False,
            "total_deployments": 0,
            "unhealthy_deployments": [],
            "error": result.error,
        }

    items = (result.data or {}).get("items", [])
    unhealthy: list[dict[str, Any]] = []

    for deployment in items:
        metadata = deployment.get("metadata", {})
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})

        issues = _deployment_issues(deployment)
        if not issues:
            continue

        unhealthy.append(
            {
                "name": metadata.get("name", "unknown"),
                "namespace": metadata.get("namespace", "default"),
                "desired_replicas": spec.get("replicas", 1),
                "available_replicas": status.get("availableReplicas", 0),
                "unavailable_replicas": status.get("unavailableReplicas", 0),
                "ready_replicas": status.get("readyReplicas", 0),
                "issues": issues,
            }
        )

    return {
        "healthy": len(unhealthy) == 0,
        "total_deployments": len(items),
        "unhealthy_deployments": unhealthy,
    }
