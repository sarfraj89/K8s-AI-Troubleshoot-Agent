from __future__ import annotations

import asyncio

from loguru import logger

from app.backend_client import BackendClient
from app.config import settings
from app.kubernetes_collector import collect_cluster_metadata, collect_evidence


async def run_agent() -> None:
    client = BackendClient()
    logger.info("Starting k8s-ai-agent cluster_id={}", settings.CLUSTER_ID)

    while True:
        try:
            metadata = collect_cluster_metadata()
            await client.heartbeat(metadata)

            job = await client.next_job()
            if job:
                logger.info("Received job {}", job["id"])
                try:
                    evidence = collect_evidence(job.get("namespace", "default"))
                    await client.submit_result(job["id"], status="completed", evidence=evidence)
                    logger.info("Submitted job result {}", job["id"])
                except Exception as exc:
                    logger.exception("Job {} failed: {}", job["id"], exc)
                    await client.submit_result(job["id"], status="failed", error=str(exc))
        except Exception as exc:
            logger.warning("Agent loop failed: {}", exc)

        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run_agent())
