from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from src.infrastructure.database.models import (
    WorkflowRunStatus,
    AgentRunStatus,
    AgentType,
)


class WorkflowStepDefinition(BaseModel):
    name: str
    agent: str  # AI_COO, BUSINESS_ANALYST, DEVELOPER, QA, KNOWLEDGE, HUMAN
    type: str
    condition: Optional[str] = None


class WorkflowDefinition(BaseModel):
    steps: List[WorkflowStepDefinition] = Field(default_factory=list)


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    definition: Dict[str, Any]


class WorkflowResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    version: int
    definition: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentResponse(BaseModel):
    id: str
    name: str
    type: AgentType
    description: Optional[str] = None
    model: str
    is_active: bool
    config: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ToolExecutionResponse(BaseModel):
    id: str
    tool_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    status: str
    started_at: datetime
    completed_at: datetime
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AgentRunResponse(BaseModel):
    id: str
    workflow_run_id: str
    agent_id: str
    task_id: Optional[str] = None
    status: AgentRunStatus
    input_context: Dict[str, Any]
    output: Dict[str, Any]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    tool_executions: List[ToolExecutionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunCreate(BaseModel):
    workflow_id: Optional[str] = None
    request_id: str


class WorkflowRunResponse(BaseModel):
    id: str
    workflow_id: str
    request_id: str
    status: WorkflowRunStatus
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    agent_runs: List[AgentRunResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

