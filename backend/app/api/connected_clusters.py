from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.ai.service import diagnose
from app.core.config import settings
from app.models.connected_cluster import ClusterProvider
from app.services.cluster_registry import registry

router = APIRouter(prefix="/connected-clusters", tags=["connected-clusters"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])


class ConnectClusterRequest(BaseModel):
    user_id: str
    name: str = Field(min_length=1, max_length=120)
    provider: ClusterProvider = ClusterProvider.CUSTOM
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestigateConnectedClusterRequest(BaseModel):
    user_id: str
    namespace: str = "default"


class AgentHeartbeatRequest(BaseModel):
    cluster_id: str
    agent_version: str | None = None
    cluster_uid: str | None = None
    kube_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentJobResultRequest(BaseModel):
    status: str = Field(pattern="^(completed|failed)$")
    evidence: dict[str, Any] | None = None
    error: str | None = None


def _backend_url() -> str:
    return (settings.PUBLIC_BACKEND_URL or "https://k8s-ai-troubleshoot-agent.onrender.com").rstrip("/")


def _helm_command(cluster_id: str, token: str) -> str:
    return (
        "helm install k8s-ai-agent ./charts/k8s-ai-agent "
        "--namespace k8s-ai-agent --create-namespace "
        f"--set backendUrl={_backend_url()} "
        f"--set clusterId={cluster_id} "
        f"--set agentToken={token}"
    )


def _agent_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def _require_agent(cluster_id: str, authorization: str | None) -> dict[str, Any]:
    token = _agent_token(authorization)
    cluster = registry.verify_agent(cluster_id, token)
    if not cluster:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    return cluster


@router.post("")
async def create_connected_cluster(request: ConnectClusterRequest):
    cluster, token = registry.create_cluster(
        user_id=request.user_id,
        name=request.name,
        provider=request.provider.value,
        metadata=request.metadata,
    )
    return {
        "cluster": cluster,
        "agent_token": token,
        "helm_command": _helm_command(cluster["id"], token),
    }


@router.get("")
async def list_connected_clusters(user_id: str):
    return {"clusters": registry.list_clusters(user_id)}


@router.get("/{cluster_id}")
async def get_connected_cluster(cluster_id: str):
    cluster = registry.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Connected cluster not found")
    return cluster


@router.post("/{cluster_id}/investigate")
async def investigate_connected_cluster(cluster_id: str, request: InvestigateConnectedClusterRequest):
    cluster = registry.get_cluster(cluster_id)
    if not cluster or cluster["user_id"] != request.user_id:
        raise HTTPException(status_code=404, detail="Connected cluster not found")
    if cluster["status"] not in ("connected", "pending"):
        raise HTTPException(status_code=409, detail="Cluster is not connected")
    job = registry.create_job(cluster_id=cluster_id, user_id=request.user_id, namespace=request.namespace)
    return {"job": job}


@agent_router.post("/heartbeat")
async def agent_heartbeat(
    request: AgentHeartbeatRequest,
    authorization: str | None = Header(default=None),
):
    _require_agent(request.cluster_id, authorization)
    cluster = registry.heartbeat(
        request.cluster_id,
        agent_version=request.agent_version,
        cluster_uid=request.cluster_uid,
        kube_version=request.kube_version,
        metadata=request.metadata,
    )
    return {"ok": True, "cluster": cluster}


@agent_router.get("/jobs/next")
async def agent_next_job(
    cluster_id: str,
    authorization: str | None = Header(default=None),
):
    _require_agent(cluster_id, authorization)
    job = registry.next_job(cluster_id)
    return {"job": job}


@agent_router.post("/jobs/{job_id}/result")
async def agent_job_result(
    job_id: str,
    request: AgentJobResultRequest,
    cluster_id: str,
    authorization: str | None = Header(default=None),
):
    _require_agent(cluster_id, authorization)

    diagnosis = None
    status = request.status
    error = request.error
    if request.status == "completed" and request.evidence:
        try:
            diagnosis = await diagnose(request.evidence)
        except Exception as exc:
            status = "failed"
            error = f"AI diagnosis failed: {exc}"

    job = registry.complete_job(
        cluster_id=cluster_id,
        job_id=job_id,
        status=status,
        evidence=request.evidence,
        diagnosis=diagnosis,
        error=error,
    )
    return {"ok": True, "job": job}
