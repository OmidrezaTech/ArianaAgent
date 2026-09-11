from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from src.infrastructure.database.models import (
    RequestType,
    RequestStatus,
    TaskType,
    TaskStatus,
)


# ----------------------------------------------------------------------
# Requests
# ----------------------------------------------------------------------
class RequestCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    request_type: RequestType = RequestType.FEATURE
    priority: int = Field(default=3, ge=1, le=5)
    auto_start_workflow: bool = True


class RequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RequestStatus] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)


class RequirementResponse(BaseModel):
    id: str
    project_id: str
    request_id: str
    title: str
    description: Optional[str] = None
    business_rules: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: int
    status: str
    version: int
    created_by_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    id: str
    project_id: str
    request_id: str
    requirement_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    task_type: TaskType
    status: TaskStatus
    priority: int
    assigned_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestResponse(BaseModel):
    id: str
    project_id: str
    created_by: str
    title: str
    description: Optional[str] = None
    request_type: RequestType
    status: RequestStatus
    priority: int
    created_at: datetime
    updated_at: datetime
    requirements: List[RequirementResponse] = Field(default_factory=list)
    tasks: List[TaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

