"""Orchestrate the full Kubernetes evidence-gathering workflow."""

from __future__ import annotations

from typing import Any, Callable

from loguru import logger

from app.kubernetes.deployment_inspector import inspect_deployments
from app.kubernetes.events_analyzer import analyze_events
from app.kubernetes.logs_collector import collect_logs
from app.kubernetes.network_inspector import inspect_network
from app.kubernetes.pod_inspector import inspect_pods


ProgressCallback = Callable[[str, str, str], None]


def run_investigation(
    on_progress: ProgressCallback | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """
    Run the full investigation pipeline like a junior DevOps engineer.

    Flow:
        1. Check pods
        2. Collect logs for problematic pods
        3. Analyze events
        4. Inspect deployments
        5. Check networking

    Returns a single structured payload with all evidence.
    """
    logger.info("Starting Kubernetes investigation (context={})", context or "default")

    if on_progress:
        on_progress("pods", "in-progress", "Checking pod health")
    pods = inspect_pods(context=context)
    if on_progress:
        on_progress("pods", "completed", "Pod inspection complete")
    logger.info(
        "Pod inspection complete — healthy={}, problematic={}",
        pods.get("healthy"),
        len(pods.get("problematic_pods", [])),
    )

    if on_progress:
        on_progress("logs", "in-progress", "Reading logs from problematic pods")
    logs = collect_logs(pods.get("problematic_pods", []), context=context)
    if on_progress:
        on_progress("logs", "completed", "Log collection complete")
    logger.info("Log collection complete — entries={}", logs.get("collected_for", 0))

    if on_progress:
        on_progress("events", "in-progress", "Analyzing Kubernetes events")
    events = analyze_events(context=context)
    if on_progress:
        on_progress("events", "completed", "Event analysis complete")
    logger.info(
        "Events analysis complete — findings={}",
        events.get("watched_reasons_found", 0),
    )

    if on_progress:
        on_progress("deployments", "in-progress", "Inspecting deployments")
    deployments = inspect_deployments(context=context)
    if on_progress:
        on_progress("deployments", "completed", "Deployment inspection complete")
    logger.info(
        "Deployment inspection complete — unhealthy={}",
        len(deployments.get("unhealthy_deployments", [])),
    )

    if on_progress:
        on_progress("network", "in-progress", "Checking services and networking")
    network = inspect_network(context=context)
    if on_progress:
        on_progress("network", "completed", "Network inspection complete")
    logger.info("Network inspection complete — issues={}", len(network.get("issues", [])))

    investigation = {
        "pods": pods,
        "logs": logs,
        "events": events,
        "deployments": deployments,
        "network": network,
        "context": context or "default",
    }

    logger.info("Kubernetes investigation finished")
    return investigation
