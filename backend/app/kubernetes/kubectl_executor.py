"""Safe kubectl command execution via subprocess."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Optional

from loguru import logger

from app.core.config import settings


@dataclass
class KubectlResult:
    """Structured result from a kubectl command."""

    success: bool
    command: str
    stdout: str
    stderr: str
    return_code: int
    data: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _build_base_command(context: str | None = None) -> list[str]:
    """Build the base kubectl command with optional kubeconfig and context."""
    cmd = ["kubectl"]
    if settings.kubeconfig:
        cmd.extend(["--kubeconfig", os.path.expanduser(settings.kubeconfig)])
    if context:
        cmd.extend(["--context", context])
    return cmd


def run_kubectl(args: list[str], timeout: int = 60, context: str | None = None) -> KubectlResult:
    """
    Execute a kubectl command safely using subprocess.

    Args:
        args: kubectl arguments (without the 'kubectl' binary name).
        timeout: seconds before the command is killed.
        context: optional kubeconfig context to use.

    Returns:
        KubectlResult with stdout, stderr, and success flag.
    """
    command = _build_base_command(context) + args
    command_str = " ".join(command)
    logger.info("Running kubectl: {}", command_str)

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        logger.error("kubectl binary not found on PATH")
        return KubectlResult(
            success=False,
            command=command_str,
            stdout="",
            stderr="",
            return_code=-1,
            error="kubectl not found. Install kubectl and ensure it is on PATH.",
        )
    except subprocess.TimeoutExpired:
        logger.error("kubectl command timed out: {}", command_str)
        return KubectlResult(
            success=False,
            command=command_str,
            stdout="",
            stderr="",
            return_code=-1,
            error=f"Command timed out after {timeout} seconds.",
        )

    result = KubectlResult(
        success=completed.returncode == 0,
        command=command_str,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        return_code=completed.returncode,
    )

    if not result.success:
        result.error = result.stderr or f"kubectl exited with code {completed.returncode}"
        logger.warning("kubectl failed: {} — {}", command_str, result.error)
    else:
        logger.debug("kubectl succeeded: {}", command_str)

    return result


def run_kubectl_json(args: list[str], timeout: int = 60, context: str | None = None) -> KubectlResult:
    """
    Run kubectl with JSON output and parse the response.

    Appends '-o json' if not already present.
    """
    json_args = list(args)
    if "-o" not in json_args:
        json_args.extend(["-o", "json"])

    result = run_kubectl(json_args, timeout=timeout, context=context)
    if not result.success or not result.stdout:
        return result

    try:
        result.data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        result.success = False
        result.error = f"Failed to parse kubectl JSON output: {exc}"
        logger.error(result.error)

    return result


def _context_metadata() -> dict[str, dict[str, str]]:
    """Return kubeconfig metadata keyed by context name."""
    result = run_kubectl_json(["config", "view"])
    if not result.success:
        return {}

    metadata: dict[str, dict[str, str]] = {}
    for item in (result.data or {}).get("contexts") or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        context = item.get("context") or {}
        if not name:
            continue
        metadata[name] = {
            "cluster": context.get("cluster", ""),
            "user": context.get("user", ""),
            "namespace": context.get("namespace", "default"),
        }
    return metadata


def _context_reachability(name: str) -> tuple[bool, str | None]:
    """Check whether kubectl can reach the selected context."""
    result = run_kubectl(["get", "--raw=/readyz"], timeout=8, context=name)
    if result.success:
        return True, None
    return False, result.error or result.stderr or "Unable to reach Kubernetes API server."


def list_kube_contexts(include_status: bool = False) -> list[dict]:
    """
    Parse the kubeconfig file and return available contexts.

    Returns:
        List of dicts with 'name' and 'is_current' keys.
    """
    result = run_kubectl(["config", "get-contexts", "-o", "name"])
    if not result.success:
        return []

    current_result = run_kubectl(["config", "current-context"])
    current_context = current_result.stdout.strip() if current_result.success else ""

    metadata = _context_metadata()
    contexts = []
    for line in result.stdout.splitlines():
        name = line.strip()
        if name:
            context = {
                "name": name,
                "is_current": name == current_context,
                **metadata.get(name, {}),
            }
            if include_status:
                reachable, error = _context_reachability(name)
                context["reachable"] = reachable
                context["status"] = "ready" if reachable else "unreachable"
                if error:
                    context["error"] = error
            contexts.append(context)
    return contexts
