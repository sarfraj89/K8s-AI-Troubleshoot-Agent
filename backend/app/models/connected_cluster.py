from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ClusterProvider(StrEnum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"
    CUSTOM = "custom"


class ConnectedClusterStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REVOKED = "revoked"


class ConnectedClusterBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: ClusterProvider = ClusterProvider.CUSTOM
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConnectedClusterCreate(ConnectedClusterBase):
    user_id: UUID


class ConnectedCluster(ConnectedClusterBase):
    id: UUID
    user_id: UUID
    status: ConnectedClusterStatus
    agent_version: str | None = None
    cluster_uid: str | None = None
    kube_version: str | None = None
    last_heartbeat_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ClusterAgentEvent(BaseModel):
    id: UUID
    cluster_id: UUID
    event_type: str
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
