from __future__ import annotations

import json
import subprocess
from typing import Any

from loguru import logger


def run_kubectl(args: list[str], timeout: int = 60) -> tuple[bool, Any, str | None]:
    command = ["kubectl", *args]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, None, "kubectl not found in agent container"
    except subprocess.TimeoutExpired:
        return False, None, f"kubectl command timed out: {' '.join(command)}"

    if completed.returncode != 0:
        return False, None, completed.stderr.strip() or f"kubectl exited with {completed.returncode}"

    if "-o" in args and "json" in args:
        try:
            return True, json.loads(completed.stdout), None
        except json.JSONDecodeError as exc:
            return False, None, f"Could not parse kubectl JSON: {exc}"

    return True, completed.stdout.strip(), None


def collect_pods() -> dict[str, Any]:
    ok, data, error = run_kubectl(["get", "pods", "-A", "-o", "json"])
    if not ok:
        return {"healthy": False, "total_pods": 0, "problematic_pods": [], "error": error}

    problematic = []
    for pod in data.get("items", []):
        meta = pod.get("metadata", {})
        status = pod.get("status", {})
        namespace = meta.get("namespace", "default")
        name = meta.get("name", "unknown")
        phase = status.get("phase", "Unknown")
        statuses = status.get("containerStatuses") or status.get("initContainerStatuses") or []
        reasons = []
        if phase in ("Pending", "Failed", "Unknown"):
            reasons.append(phase)
        for container in statuses:
            waiting = container.get("state", {}).get("waiting", {})
            terminated = container.get("state", {}).get("terminated", {})
            reason = waiting.get("reason") or terminated.get("reason")
            if reason and reason not in ("Completed",):
                reasons.append(reason)
        for reason in dict.fromkeys(reasons):
            problematic.append({"name": name, "namespace": namespace, "status": reason, "phase": phase})

    return {"healthy": len(problematic) == 0, "total_pods": len(data.get("items", [])), "problematic_pods": problematic}


def collect_logs(problematic_pods: list[dict[str, str]]) -> dict[str, Any]:
    entries = {}
    for pod in problematic_pods[:10]:
        namespace = pod.get("namespace", "default")
        name = pod.get("name", "")
        ok, output, error = run_kubectl(["logs", name, "-n", namespace, "--all-containers", "--tail=80"], timeout=30)
        lines = output.splitlines() if ok and isinstance(output, str) else []
        entries[f"{namespace}/{name}"] = {
            "namespace": namespace,
            "pod": name,
            "status": pod.get("status"),
            "lines": lines,
            "message": None if ok else error,
        }
    return {"collected_for": len(entries), "entries": entries}


def collect_events() -> dict[str, Any]:
    ok, data, error = run_kubectl(["get", "events", "-A", "--sort-by=.lastTimestamp", "-o", "json"])
    if not ok:
        return {"healthy": False, "total_events": 0, "findings": [], "error": error}
    watched = {"FailedScheduling", "BackOff", "FailedMount", "FailedPull", "ErrImagePull", "Unhealthy"}
    findings = {}
    for event in data.get("items", []):
        reason = event.get("reason")
        if reason not in watched:
            continue
        involved = event.get("involvedObject", {})
        findings.setdefault(reason, []).append(
            {
                "namespace": involved.get("namespace", "default"),
                "resource": involved.get("kind", "Unknown"),
                "name": involved.get("name", "unknown"),
                "message": event.get("message", ""),
                "type": event.get("type", "Normal"),
                "count": str(event.get("count", 1)),
            }
        )
    grouped = [{"reason": reason, "count": len(items), "examples": items[-3:]} for reason, items in findings.items()]
    grouped.sort(key=lambda item: item["count"], reverse=True)
    return {"healthy": len(grouped) == 0, "total_events": len(data.get("items", [])), "watched_reasons_found": len(grouped), "findings": grouped}


def collect_deployments() -> dict[str, Any]:
    ok, data, error = run_kubectl(["get", "deployments", "-A", "-o", "json"])
    if not ok:
        return {"healthy": False, "total_deployments": 0, "unhealthy_deployments": [], "error": error}
    unhealthy = []
    for deployment in data.get("items", []):
        meta = deployment.get("metadata", {})
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})
        desired = spec.get("replicas", 1)
        available = status.get("availableReplicas", 0)
        ready = status.get("readyReplicas", 0)
        if available < desired or ready < desired:
            unhealthy.append(
                {
                    "name": meta.get("name"),
                    "namespace": meta.get("namespace", "default"),
                    "desired_replicas": desired,
                    "available_replicas": available,
                    "ready_replicas": ready,
                    "issues": [f"Only {available}/{desired} replicas available"],
                }
            )
    return {"healthy": len(unhealthy) == 0, "total_deployments": len(data.get("items", [])), "unhealthy_deployments": unhealthy}


def collect_network() -> dict[str, Any]:
    ok, data, error = run_kubectl(["get", "svc", "-A", "-o", "json"])
    if not ok:
        return {"healthy": False, "total_services": 0, "issues": [], "error": error}
    return {"healthy": True, "total_services": len(data.get("items", [])), "issues": []}


def collect_cluster_metadata() -> dict[str, str | None]:
    ok, version, _error = run_kubectl(["version", "-o", "json"], timeout=15)
    kube_version = None
    if ok and isinstance(version, dict):
        kube_version = version.get("serverVersion", {}).get("gitVersion")
    ok, ns_data, _error = run_kubectl(["get", "namespace", "kube-system", "-o", "json"], timeout=15)
    cluster_uid = None
    if ok and isinstance(ns_data, dict):
        cluster_uid = ns_data.get("metadata", {}).get("uid")
    return {"kube_version": kube_version, "cluster_uid": cluster_uid}


def collect_evidence(namespace: str = "default") -> dict[str, Any]:
    logger.info("Collecting Kubernetes evidence namespace={}", namespace)
    pods = collect_pods()
    return {
        "pods": pods,
        "logs": collect_logs(pods.get("problematic_pods", [])),
        "events": collect_events(),
        "deployments": collect_deployments(),
        "network": collect_network(),
        "context": "in-cluster-agent",
        "namespace": namespace,
    }
