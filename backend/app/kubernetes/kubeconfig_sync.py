"""Keep the container's kubeconfig in sync with the live host kubeconfig.

The host kubeconfig lists kind clusters with a `https://127.0.0.1:<port>` API
server, which is unreachable from inside a container. This module copies the
live host config to a writable location and rewrites every kind cluster's
server to its in-network address (`https://<cluster>-control-plane:6443`), which
is reachable because the backend is attached to the shared `kind` Docker network.

Running this on each /clusters and /investigate call means new clusters the user
spins up appear (and work) without restarting the backend.
"""

from __future__ import annotations

import os
import shutil
import subprocess

from loguru import logger

from app.core.config import settings

# Read-only bind mount of the user's ~/.kube directory (see docker-compose.yml).
HOST_KUBECONFIG = os.environ.get("HOST_KUBECONFIG", "/host-kube/config")


def _target_path() -> str:
    return os.path.expanduser(settings.kubeconfig or "/root/.kube/config")


def sync_kubeconfig() -> None:
    """Regenerate the container kubeconfig from the live host kubeconfig."""
    if not os.path.exists(HOST_KUBECONFIG):
        # Running outside Docker (or no mount) — leave the configured file as-is.
        logger.debug("Host kubeconfig not found at {}; skipping sync", HOST_KUBECONFIG)
        return

    target = _target_path()
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(HOST_KUBECONFIG, target)
    except OSError as exc:
        logger.warning("Could not sync kubeconfig from {} to {}: {}", HOST_KUBECONFIG, target, exc)
        return

    try:
        clusters = subprocess.run(
            ["kubectl", "--kubeconfig", target, "config", "get-clusters"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        logger.warning("kubectl not found; kubeconfig sync skipped")
        return

    for line in clusters.stdout.splitlines():
        name = line.strip()
        if not name or name.upper() == "NAME":
            continue
        if not name.startswith("kind-"):
            continue

        # kind cluster "kind-X" -> control-plane container "X-control-plane".
        cluster = name[len("kind-"):]
        server = f"https://{cluster}-control-plane:6443"
        try:
            subprocess.run(
                ["kubectl", "--kubeconfig", target, "config", "set-cluster", name, f"--server={server}"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            logger.warning("kubectl not found; kubeconfig sync stopped")
            return
        logger.info("kubeconfig sync: {} -> {}", name, server)
