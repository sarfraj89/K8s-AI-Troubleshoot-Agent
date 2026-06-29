"""Collect concise logs from failed or unhealthy pods."""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from app.kubernetes.kubectl_executor import run_kubectl

# Lines matching these patterns are considered relevant for troubleshooting.
RELEVANT_PATTERNS = [
    re.compile(r"exception", re.IGNORECASE),
    re.compile(r"traceback", re.IGNORECASE),
    re.compile(r"error", re.IGNORECASE),
    re.compile(r"fatal", re.IGNORECASE),
    re.compile(r"failed", re.IGNORECASE),
    re.compile(r"connection refused", re.IGNORECASE),
    re.compile(r"connection error", re.IGNORECASE),
    re.compile(r"no such file", re.IGNORECASE),
    re.compile(r"env", re.IGNORECASE),
    re.compile(r"environment variable", re.IGNORECASE),
    re.compile(r"imagepullbackoff", re.IGNORECASE),
    re.compile(r"errimagepull", re.IGNORECASE),
    re.compile(r"crashloopbackoff", re.IGNORECASE),
    re.compile(r"oomkilled", re.IGNORECASE),
    re.compile(r"startup", re.IGNORECASE),
    re.compile(r"permission denied", re.IGNORECASE),
    re.compile(r"cannot find", re.IGNORECASE),
    re.compile(r"not found", re.IGNORECASE),
]

MAX_TAIL_LINES = 80
MAX_RELEVANT_LINES = 25
STATUSES_NEEDING_PREVIOUS_LOGS = {"CrashLoopBackOff", "Error", "OOMKilled"}


def _is_relevant(line: str) -> bool:
    return any(pattern.search(line) for pattern in RELEVANT_PATTERNS)


def _extract_relevant_lines(raw_logs: str) -> list[str]:
    """Keep only lines that look like failures; fall back to last few lines."""
    lines = [line for line in raw_logs.splitlines() if line.strip()]
    if not lines:
        return []

    relevant = [line for line in lines if _is_relevant(line)]
    if relevant:
        return relevant[-MAX_RELEVANT_LINES:]

    return lines[-10:]


def _fetch_pod_logs(namespace: str, pod_name: str, previous: bool = False, context: str | None = None) -> str:
    args = ["logs", pod_name, "-n", namespace, "--all-containers", f"--tail={MAX_TAIL_LINES}"]
    if previous:
        args.append("--previous")

    result = run_kubectl(args, timeout=30, context=context)
    if result.success:
        return result.stdout

    if previous:
        return ""

    logger.debug("Could not fetch logs for {}/{}: {}", namespace, pod_name, result.error)
    return ""


def collect_logs(problematic_pods: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
    """
    Fetch logs for failed pods and return concise, relevant excerpts.

    Args:
        problematic_pods: list from pod_inspector with name, namespace, status keys.

    Returns:
        Structured dict keyed by "namespace/pod" with log excerpts.
    """
    if not problematic_pods:
        return {"collected_for": 0, "entries": {}, "message": "No problematic pods to collect logs from."}

    # Deduplicate by namespace/name — one log fetch per pod.
    seen: set[tuple[str, str]] = set()
    entries: dict[str, Any] = {}

    for pod in problematic_pods:
        namespace = pod.get("namespace", "default")
        name = pod.get("name", "")
        status = pod.get("status", "")

        key_tuple = (namespace, name)
        if not name or key_tuple in seen:
            continue
        seen.add(key_tuple)

        pod_key = f"{namespace}/{name}"
        raw_logs = _fetch_pod_logs(namespace, name, context=context)

        if status in STATUSES_NEEDING_PREVIOUS_LOGS:
            previous_logs = _fetch_pod_logs(namespace, name, previous=True, context=context)
            if previous_logs:
                raw_logs = previous_logs if not raw_logs else f"{raw_logs}\n--- previous container ---\n{previous_logs}"

        if not raw_logs:
            entries[pod_key] = {
                "namespace": namespace,
                "pod": name,
                "status": status,
                "lines": [],
                "message": "No logs available (pod may not have started yet).",
            }
            continue

        relevant_lines = _extract_relevant_lines(raw_logs)
        entries[pod_key] = {
            "namespace": namespace,
            "pod": name,
            "status": status,
            "line_count": len(relevant_lines),
            "lines": relevant_lines,
        }

    return {
        "collected_for": len(entries),
        "entries": entries,
    }
