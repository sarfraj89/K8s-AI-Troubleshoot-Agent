"""Demo Kubernetes evidence for deployments without cluster access."""

from __future__ import annotations

from typing import Any, Callable


ProgressCallback = Callable[[str, str, str], None]


DEMO_CONTEXT = {
    "name": "demo-crashloop-cluster",
    "is_current": True,
    "cluster": "demo-crashloop-cluster",
    "namespace": "production",
    "reachable": True,
    "status": "ready",
}


def run_mock_investigation(
    on_progress: ProgressCallback | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """Return realistic Kubernetes troubleshooting evidence for demo mode."""
    steps = [
        ("pods", "Checking pod health", "Pod inspection complete"),
        ("logs", "Reading logs from problematic pods", "Log collection complete"),
        ("events", "Analyzing Kubernetes events", "Event analysis complete"),
        ("deployments", "Inspecting deployments", "Deployment inspection complete"),
        ("network", "Checking services and networking", "Network inspection complete"),
    ]

    for step, start, done in steps:
        if on_progress:
            on_progress(step, "in-progress", start)
            on_progress(step, "completed", done)

    return {
        "pods": {
            "healthy": False,
            "total_pods": 7,
            "problematic_pods": [
                {
                    "name": "checkout-api-6b9f7d6f9c-k2p7x",
                    "namespace": "production",
                    "status": "CrashLoopBackOff",
                    "phase": "Running",
                },
                {
                    "name": "checkout-api-6b9f7d6f9c-w8m4q",
                    "namespace": "production",
                    "status": "CrashLoopBackOff",
                    "phase": "Running",
                },
            ],
        },
        "logs": {
            "collected_for": 2,
            "entries": {
                "production/checkout-api-6b9f7d6f9c-k2p7x": {
                    "namespace": "production",
                    "pod": "checkout-api-6b9f7d6f9c-k2p7x",
                    "status": "CrashLoopBackOff",
                    "line_count": 5,
                    "lines": [
                        "Starting checkout-api service",
                        "ERROR Missing required environment variable: DATABASE_URL",
                        "Traceback: ConfigError: DATABASE_URL is not configured",
                        "Application startup failed",
                        "Process exited with code 1",
                    ],
                },
                "production/checkout-api-6b9f7d6f9c-w8m4q": {
                    "namespace": "production",
                    "pod": "checkout-api-6b9f7d6f9c-w8m4q",
                    "status": "CrashLoopBackOff",
                    "line_count": 4,
                    "lines": [
                        "Starting checkout-api service",
                        "ERROR Missing required environment variable: DATABASE_URL",
                        "Application startup failed",
                        "Process exited with code 1",
                    ],
                },
            },
        },
        "events": {
            "healthy": False,
            "total_events": 18,
            "watched_reasons_found": 2,
            "findings": [
                {
                    "reason": "BackOff",
                    "count": 8,
                    "examples": [
                        {
                            "namespace": "production",
                            "resource": "Pod",
                            "name": "checkout-api-6b9f7d6f9c-k2p7x",
                            "message": "Back-off restarting failed container checkout-api",
                            "type": "Warning",
                            "count": "8",
                        }
                    ],
                },
                {
                    "reason": "Unhealthy",
                    "count": 3,
                    "examples": [
                        {
                            "namespace": "production",
                            "resource": "Pod",
                            "name": "checkout-api-6b9f7d6f9c-k2p7x",
                            "message": "Readiness probe failed: connection refused",
                            "type": "Warning",
                            "count": "3",
                        }
                    ],
                },
            ],
        },
        "deployments": {
            "healthy": False,
            "total_deployments": 3,
            "unhealthy_deployments": [
                {
                    "name": "checkout-api",
                    "namespace": "production",
                    "desired_replicas": 2,
                    "available_replicas": 0,
                    "unavailable_replicas": 2,
                    "ready_replicas": 0,
                    "issues": [
                        "Only 0/2 replicas available",
                        "2 unavailable replica(s)",
                        "Only 0/2 replicas ready",
                    ],
                }
            ],
        },
        "network": {
            "healthy": False,
            "total_services": 4,
            "issues": [
                {
                    "service": "checkout-api",
                    "namespace": "production",
                    "type": "ClusterIP",
                    "issue": "Missing endpoints - service has no ready backends",
                    "matching_pods": 2,
                    "selector": {"app": "checkout-api"},
                }
            ],
        },
        "context": context or DEMO_CONTEXT["name"],
        "mode": "demo",
    }
