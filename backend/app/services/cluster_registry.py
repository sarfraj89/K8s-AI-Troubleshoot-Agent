from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings


STORE_VERSION = 1
_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_agent_token() -> str:
    return f"k8sai_{secrets.token_urlsafe(32)}"


class ClusterRegistry:
    """Small file-backed control-plane store for connected cluster MVP.

    This intentionally keeps the Phase 2 agent protocol usable before the
    InsForge service-role persistence layer is wired in.
    """

    def __init__(self, path: str | None = None):
        self.path = Path(path or settings.AGENT_STORE_PATH)

    def _empty(self) -> dict[str, Any]:
        return {"version": STORE_VERSION, "clusters": {}, "jobs": {}, "events": []}

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        data.setdefault("version", STORE_VERSION)
        data.setdefault("clusters", {})
        data.setdefault("jobs", {})
        data.setdefault("events", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, self.path)

    def _event(
        self,
        data: dict[str, Any],
        cluster_id: str,
        event_type: str,
        message: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        data["events"].append(
            {
                "id": str(uuid4()),
                "cluster_id": cluster_id,
                "event_type": event_type,
                "message": message,
                "payload": payload or {},
                "created_at": utc_now(),
            }
        )

    def create_cluster(
        self,
        *,
        user_id: str,
        name: str,
        provider: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        token = generate_agent_token()
        cluster_id = str(uuid4())
        now = utc_now()
        cluster = {
            "id": cluster_id,
            "user_id": user_id,
            "name": name,
            "provider": provider,
            "status": "pending",
            "agent_token_hash": hash_token(token),
            "agent_version": None,
            "cluster_uid": None,
            "kube_version": None,
            "last_heartbeat_at": None,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }

        with _LOCK:
            data = self._read()
            data["clusters"][cluster_id] = cluster
            self._event(data, cluster_id, "cluster.created", "Cluster connection created")
            self._write(data)

        return self.public_cluster(cluster), token

    def list_clusters(self, user_id: str) -> list[dict[str, Any]]:
        with _LOCK:
            data = self._read()
        clusters = [
            self.public_cluster(cluster)
            for cluster in data["clusters"].values()
            if cluster.get("user_id") == user_id
        ]
        return sorted(clusters, key=lambda item: item["created_at"], reverse=True)

    def get_cluster(self, cluster_id: str) -> dict[str, Any] | None:
        with _LOCK:
            data = self._read()
        cluster = data["clusters"].get(cluster_id)
        return self.public_cluster(cluster) if cluster else None

    def verify_agent(self, cluster_id: str, token: str) -> dict[str, Any] | None:
        with _LOCK:
            data = self._read()
        cluster = data["clusters"].get(cluster_id)
        if not cluster or cluster.get("status") == "revoked":
            return None
        if secrets.compare_digest(cluster.get("agent_token_hash", ""), hash_token(token)):
            return cluster
        return None

    def heartbeat(
        self,
        cluster_id: str,
        *,
        agent_version: str | None = None,
        cluster_uid: str | None = None,
        kube_version: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with _LOCK:
            data = self._read()
            cluster = data["clusters"][cluster_id]
            cluster["status"] = "connected"
            cluster["last_heartbeat_at"] = utc_now()
            cluster["updated_at"] = cluster["last_heartbeat_at"]
            if agent_version:
                cluster["agent_version"] = agent_version
            if cluster_uid:
                cluster["cluster_uid"] = cluster_uid
            if kube_version:
                cluster["kube_version"] = kube_version
            if metadata:
                cluster["metadata"] = {**cluster.get("metadata", {}), **metadata}
            self._event(data, cluster_id, "agent.heartbeat", "Agent heartbeat received")
            self._write(data)
            return self.public_cluster(cluster)

    def create_job(self, *, cluster_id: str, user_id: str, namespace: str = "default") -> dict[str, Any]:
        job_id = str(uuid4())
        now = utc_now()
        job = {
            "id": job_id,
            "cluster_id": cluster_id,
            "user_id": user_id,
            "type": "investigate",
            "namespace": namespace,
            "status": "queued",
            "requested_at": now,
            "started_at": None,
            "completed_at": None,
            "evidence": None,
            "diagnosis": None,
            "error": None,
        }
        with _LOCK:
            data = self._read()
            data["jobs"][job_id] = job
            self._event(data, cluster_id, "job.queued", "Investigation job queued", {"job_id": job_id})
            self._write(data)
        return job

    def next_job(self, cluster_id: str) -> dict[str, Any] | None:
        with _LOCK:
            data = self._read()
            queued = [
                job
                for job in data["jobs"].values()
                if job.get("cluster_id") == cluster_id and job.get("status") == "queued"
            ]
            if not queued:
                return None
            job = sorted(queued, key=lambda item: item["requested_at"])[0]
            job["status"] = "running"
            job["started_at"] = utc_now()
            self._event(data, cluster_id, "job.started", "Investigation job started", {"job_id": job["id"]})
            self._write(data)
            return job

    def complete_job(
        self,
        *,
        cluster_id: str,
        job_id: str,
        status: str,
        evidence: dict[str, Any] | None = None,
        diagnosis: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        with _LOCK:
            data = self._read()
            job = data["jobs"][job_id]
            if job["cluster_id"] != cluster_id:
                raise KeyError("Job does not belong to cluster")
            job["status"] = status
            job["completed_at"] = utc_now()
            job["evidence"] = evidence
            job["diagnosis"] = diagnosis
            job["error"] = error
            self._event(
                data,
                cluster_id,
                f"job.{status}",
                "Investigation job finished",
                {"job_id": job_id, "status": status},
            )
            self._write(data)
            return job

    def public_cluster(self, cluster: dict[str, Any]) -> dict[str, Any]:
        public = dict(cluster)
        public.pop("agent_token_hash", None)
        return public


registry = ClusterRegistry()
