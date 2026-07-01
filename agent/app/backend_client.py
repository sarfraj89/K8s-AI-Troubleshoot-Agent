from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class BackendClient:
    def __init__(self):
        self.base_url = settings.BACKEND_URL.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.AGENT_TOKEN}"}

    async def heartbeat(self, metadata: dict[str, Any]) -> None:
        payload = {
            "cluster_id": settings.CLUSTER_ID,
            "agent_version": settings.AGENT_VERSION,
            **metadata,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{self.base_url}/agent/heartbeat", json=payload, headers=self.headers)
            response.raise_for_status()

    async def next_job(self) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base_url}/agent/jobs/next",
                params={"cluster_id": settings.CLUSTER_ID},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json().get("job")

    async def submit_result(
        self,
        job_id: str,
        *,
        status: str,
        evidence: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        payload = {"status": status, "evidence": evidence, "error": error}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/agent/jobs/{job_id}/result",
                params={"cluster_id": settings.CLUSTER_ID},
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
