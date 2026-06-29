"""Generate actionable fix recommendations from AI analysis."""

from __future__ import annotations

from typing import Any


def _primary_resource(investigation: dict[str, Any]) -> tuple[str, str, str]:
    """
    Pick the most relevant namespace/name/kind from investigation evidence.

    Returns:
        (namespace, name, kind) — kind is 'deployment' or 'pod'.
    """
    unhealthy = investigation.get("deployments", {}).get("unhealthy_deployments", [])
    if unhealthy:
        dep = unhealthy[0]
        return dep.get("namespace", "default"), dep.get("name", ""), "deployment"

    problematic = investigation.get("pods", {}).get("problematic_pods", [])
    if problematic:
        pod = problematic[0]
        return pod.get("namespace", "default"), pod.get("name", ""), "pod"

    return "default", "", "pod"


def _ensure_kubectl_commands(
    commands: list[str] | str | None,
    namespace: str,
    name: str,
    kind: str,
) -> list[str]:
    """Ensure at least one practical kubectl command is present."""
    if isinstance(commands, str):
        commands = [commands] if commands.strip() else []
    elif commands is None:
        commands = []
    else:
        commands = [cmd for cmd in commands if cmd and cmd.strip()]

    if commands:
        return commands

    if not name:
        return ["kubectl get pods -A", "kubectl get events -A --sort-by=.lastTimestamp"]

    if kind == "deployment":
        return [
            f"kubectl describe deployment {name} -n {namespace}",
            f"kubectl edit deployment {name} -n {namespace}",
            f"kubectl rollout restart deployment {name} -n {namespace}",
        ]

    return [
        f"kubectl describe pod {name} -n {namespace}",
        f"kubectl logs {name} -n {namespace} --all-containers --tail=50",
    ]


def build_fix_recommendation(
    analysis: dict[str, Any],
    investigation: dict[str, Any],
) -> dict[str, Any]:
    """
    Build actionable fix recommendations from LLM analysis and investigation evidence.

    Enriches kubectl commands with real resource names from the cluster when missing.
    """
    namespace, name, kind = _primary_resource(investigation)

    fix_text = analysis.get("fix", "").strip()
    prevention = analysis.get("prevention_recommendation", "").strip()
    commands = _ensure_kubectl_commands(
        analysis.get("kubectl_commands") or analysis.get("kubectl_command"),
        namespace,
        name,
        kind,
    )

    # Expose a single primary command for the API while keeping the full list.
    primary_command = commands[0] if commands else ""

    return {
        "fix": fix_text or "Review the identified root cause and apply the suggested kubectl commands.",
        "kubectl_command": primary_command,
        "kubectl_commands": commands,
        "prevention_recommendation": prevention or "Add monitoring and readiness probes to catch failures early.",
    }
