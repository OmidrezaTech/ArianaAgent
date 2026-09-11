from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict
from src.infrastructure.database.models import ApprovalType, ApprovalStatus


class ApprovalCreate(BaseModel):
    project_id: str
    request_id: str
    workflow_run_id: str
    agent_run_id: Optional[str] = None
    type: ApprovalType
    requested_from: str


class ApprovalAction(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    project_id: str
    request_id: str
    workflow_run_id: str
    agent_run_id: Optional[str] = None
    type: ApprovalType
    status: ApprovalStatus
    requested_from: str
    comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

