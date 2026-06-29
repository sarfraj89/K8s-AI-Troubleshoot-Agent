"""Inspect services and networking for common misconfigurations."""

from __future__ import annotations

from typing import Any

from app.kubernetes.kubectl_executor import run_kubectl_json


def _selector_matches_pod_labels(selector: dict[str, str], labels: dict[str, str]) -> bool:
    """Return True when every selector key/value exists on the pod labels."""
    if not selector:
        return False
    return all(labels.get(key) == value for key, value in selector.items())


def inspect_network(context: str | None = None) -> dict[str, Any]:
    """
    Inspect services and endpoints for networking issues.

    Detects missing endpoints, selector mismatches, and headless/DNS-related gaps.
    """
    svc_result = run_kubectl_json(["get", "svc", "-A"], context=context)
    if not svc_result.success:
        return {
            "healthy": False,
            "total_services": 0,
            "issues": [],
            "error": svc_result.error,
        }

    pods_result = run_kubectl_json(["get", "pods", "-A"], context=context)
    endpoints_result = run_kubectl_json(["get", "endpoints", "-A"], context=context)

    services = (svc_result.data or {}).get("items", [])
    pods = (pods_result.data or {}).get("items", []) if pods_result.success else []
    endpoints_items = (endpoints_result.data or {}).get("items", []) if endpoints_result.success else []

    # Build a lookup: (namespace, service_name) -> endpoint addresses count.
    endpoint_lookup: dict[tuple[str, str], int] = {}
    for ep in endpoints_items:
        metadata = ep.get("metadata", {})
        ns = metadata.get("namespace", "default")
        name = metadata.get("name", "")
        address_count = 0
        for subset in ep.get("subsets", []) or []:
            address_count += len(subset.get("addresses", []) or [])
        endpoint_lookup[(ns, name)] = address_count

    issues: list[dict[str, Any]] = []

    for svc in services:
        metadata = svc.get("metadata", {})
        spec = svc.get("spec", {})
        namespace = metadata.get("namespace", "default")
        name = metadata.get("name", "unknown")
        selector = spec.get("selector") or {}
        svc_type = spec.get("type", "ClusterIP")
        cluster_ip = spec.get("clusterIP", "")

        # Skip the built-in Kubernetes API service (no selector by design).
        if namespace == "default" and name == "kubernetes":
            continue

        # Skip ExternalName services — they point outside the cluster.
        if svc_type == "ExternalName":
            continue

        # Skip Kubernetes system services that intentionally have no selector.
        if not selector and svc_type == "ClusterIP" and cluster_ip not in ("None", ""):
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "type": svc_type,
                    "issue": "Service has no pod selector",
                    "detail": "Traffic may not reach any pods unless manually configured.",
                }
            )
            continue

        if not selector:
            continue

        matching_pods = [
            pod
            for pod in pods
            if pod.get("metadata", {}).get("namespace") == namespace
            and _selector_matches_pod_labels(selector, pod.get("metadata", {}).get("labels", {}))
        ]

        if not matching_pods:
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "type": svc_type,
                    "issue": "Selector mismatch — no pods match service selector",
                    "selector": selector,
                }
            )
            continue

        endpoint_count = endpoint_lookup.get((namespace, name), 0)
        if endpoint_count == 0:
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "type": svc_type,
                    "issue": "Missing endpoints — service has no ready backends",
                    "matching_pods": len(matching_pods),
                    "selector": selector,
                }
            )

        # Headless services (clusterIP: None) rely on DNS A/AAAA records per pod.
        if cluster_ip == "None" and endpoint_count == 0:
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "type": svc_type,
                    "issue": "Headless service with no endpoints — DNS records may be missing",
                    "selector": selector,
                }
            )

    return {
        "healthy": len(issues) == 0,
        "total_services": len(services),
        "issues": issues,
    }
