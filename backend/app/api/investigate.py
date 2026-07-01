from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.ai.service import diagnose
from app.core.config import settings
from app.kubernetes.investigation_service import run_investigation
from app.kubernetes.kubeconfig_sync import sync_kubeconfig
from app.kubernetes.kubectl_executor import list_kube_contexts, run_kubectl
from app.kubernetes.mock_investigation import DEMO_CONTEXT, run_mock_investigation
from app.services.progress_publisher import ProgressPublisher

router = APIRouter()


class InvestigationRequest(BaseModel):
    user_id: str | None = None
    progress_channel: str | None = None
    namespace: str = "default"
    context: str | None = None


def _find_context(context_name: str | None) -> dict | None:
    """Return the selected kube context from the synced kubeconfig."""
    contexts = list_kube_contexts(include_status=True)
    if context_name:
        return next((ctx for ctx in contexts if ctx["name"] == context_name), None)
    return next((ctx for ctx in contexts if ctx.get("is_current")), contexts[0] if contexts else None)


def _friendly_kubectl_error(error: str | None) -> str:
    """Convert raw kubectl errors into beginner-friendly messages."""
    if not error:
        return "Unknown error connecting to Kubernetes cluster."

    err = error.lower()

    if "kubectl not found" in err or "no such file" in err:
        return (
            "kubectl is not installed or not on PATH.\n"
            "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
        )

    if "no such host" in err or "connection refused" in err or "dial tcp" in err:
        return (
            "Unable to connect to Kubernetes cluster.\n"
            "Please verify:\n"
            "- Your cluster is running\n"
            "- kubeconfig points to the correct cluster\n"
            "- kubectl permissions are configured"
        )

    if "unauthorized" in err or "forbidden" in err:
        return (
            "Access denied to Kubernetes cluster.\n"
            "Please verify kubectl has the required permissions."
        )

    if "kubeconfig" in err or "no configuration" in err:
        return (
            "kubeconfig not found or invalid.\n"
            "Please verify:\n"
            "- KUBECONFIG_PATH is set correctly in backend/.env\n"
            "- The kubeconfig file exists and is readable"
        )

    if "context" in err and ("not found" in err or "does not exist" in err):
        return (
            "The selected Kubernetes context was not found.\n"
            "Please select a different cluster from the list."
        )

    if "timed out" in err:
        return (
            "Connection to Kubernetes cluster timed out.\n"
            "Check that the cluster is reachable and responsive."
        )

    return error


@router.get("/clusters")
async def list_clusters():
    """
    List all available Kubernetes contexts from the kubeconfig file.
    """
    if settings.DEMO_MODE:
        return {
            "contexts": [DEMO_CONTEXT],
            "count": 1,
            "mode": "demo",
            "demo_mode": True,
        }

    # Pick up any clusters created since startup and refresh kind addresses.
    sync_kubeconfig()

    # Validate kubectl is accessible
    health_check = run_kubectl(["version", "--client"], timeout=10)
    if not health_check.success and "not found" in (health_check.error or "").lower():
        raise HTTPException(
            status_code=503,
            detail=_friendly_kubectl_error(health_check.error),
        )

    contexts = list_kube_contexts(include_status=True)

    return {
        "contexts": contexts,
        "count": len(contexts),
        "mode": "local",
        "demo_mode": False,
    }


@router.post("/investigate")
async def investigate(request: InvestigationRequest | None = None):
    """
    Investigate the Kubernetes cluster and return AI-powered diagnosis.

    Flow:
        1. Collect evidence (pods, logs, events, deployments, network)
        2. Send evidence to AI agent for root cause analysis
        3. Return structured diagnosis with fix recommendations
    """
    progress_channel = request.progress_channel if request else None
    context = request.context if request else None

    # Ensure the kubeconfig reflects current clusters before investigating.
    if not settings.DEMO_MODE:
        sync_kubeconfig()
        selected_context = _find_context(context)
        if not selected_context:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Selected Kubernetes context was not found. "
                    "Refresh the cluster list and choose an available context."
                ),
            )
        if not selected_context.get("reachable"):
            detail = selected_context.get("error") or "Kubernetes API server is not reachable."
            raise HTTPException(
                status_code=503,
                detail=_friendly_kubectl_error(detail),
            )
        context = selected_context["name"]

    with ProgressPublisher(progress_channel) as progress:
        try:
            investigation = (
                run_mock_investigation(progress.publish, context=context)
                if settings.DEMO_MODE
                else run_investigation(progress.publish, context=context)
            )
        except FileNotFoundError:
            progress.publish("complete", "error", "kubectl not found")
            raise HTTPException(
                status_code=503,
                detail=_friendly_kubectl_error("kubectl not found"),
            )
        except Exception as exc:
            progress.publish("complete", "error", "Investigation failed")
            logger.exception("Investigation failed: {}", exc)
            friendly = _friendly_kubectl_error(str(exc))
            raise HTTPException(
                status_code=500,
                detail=friendly,
            ) from exc

        # Check if kubectl commands actually worked (pods step is the canary)
        pods = investigation.get("pods", {})
        if pods.get("error") and not pods.get("total_pods"):
            err = pods["error"]
            progress.publish("complete", "error", "Cluster unreachable")
            raise HTTPException(
                status_code=503,
                detail=_friendly_kubectl_error(err),
            )

        try:
            progress.publish("ai", "in-progress", "Running AI root cause analysis")
            diagnosis = await diagnose(investigation)
            progress.publish("ai", "completed", "AI reasoning complete")
            progress.publish("complete", "completed", "Root cause found")
        except Exception as exc:
            progress.publish("ai", "error", "AI diagnosis failed")
            logger.exception("AI diagnosis failed: {}", exc)
            raise HTTPException(
                status_code=500,
                detail=f"AI diagnosis failed: {exc}",
            ) from exc

    return {
        "status": "success",
        "investigation": investigation,
        "diagnosis": diagnosis,
        "namespace": request.namespace if request else "default",
        "context": context,
    }
