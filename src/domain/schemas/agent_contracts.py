from typing import Any, List, Optional, Literal, Dict
from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# Base Agent Input / Output
# ----------------------------------------------------------------------

class AgentInput(BaseModel):
    task_id: Optional[str] = None
    project_id: str
    request_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    company_knowledge: List[str] = Field(default_factory=list)
    project_knowledge: List[str] = Field(default_factory=list)


class AgentOutput(BaseModel):
    status: Literal["SUCCESS", "FAILED", "NEEDS_APPROVAL", "REVISE"] = "SUCCESS"
    result: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    error_message: Optional[str] = None


# ----------------------------------------------------------------------
# COO Agent Contracts
# ----------------------------------------------------------------------

class WorkflowStepPlan(BaseModel):
    name: str
    agent: str
    type: str
    description: str
    condition: Optional[str] = None


class COOOutputContract(BaseModel):
    summary: str
    request_type: str
    priority_level: int = 3
    workflow_steps: List[WorkflowStepPlan] = Field(default_factory=list)
    required_agents: List[str] = Field(default_factory=list)
    estimated_complexity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    reasoning: str


# ----------------------------------------------------------------------
# Business Analyst Agent Contracts
# ----------------------------------------------------------------------

class RequirementItem(BaseModel):
    title: str
    description: str
    priority: int = 3
    business_rules: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)


class BAOutputContract(BaseModel):
    title: str
    summary: str
    requirements: List[RequirementItem] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    business_rules: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)


# ----------------------------------------------------------------------
# Developer Agent Contracts
# ----------------------------------------------------------------------

class FileOperation(BaseModel):
    path: str
    action: Literal["CREATE", "EDIT", "DELETE"]
    content: Optional[str] = None
    diff_summary: Optional[str] = None


class DevOutputContract(BaseModel):
    technical_plan: List[str] = Field(default_factory=list)
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    tests_created: List[str] = Field(default_factory=list)
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    summary: str
    all_tests_passed: bool = True


# ----------------------------------------------------------------------
# QA Agent Contracts
# ----------------------------------------------------------------------

class BugReport(BaseModel):
    title: str
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    reproduction_steps: List[str] = Field(default_factory=list)
    expected_result: str
    actual_result: str


class QAOutputContract(BaseModel):
    status: Literal["PASSED", "FAILED"]
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    coverage_percentage: float = 100.0
    bugs: List[BugReport] = Field(default_factory=list)
    requirement_verification: Dict[str, bool] = Field(default_factory=dict)
    summary: str


# ----------------------------------------------------------------------
# Knowledge Manager Agent Contracts
# ----------------------------------------------------------------------

class KnowledgeInsight(BaseModel):
    category: Literal["LESSON", "PATTERN", "FEEDBACK", "ARCHITECTURE_DECISION"]
    content: str
    importance: int = 5


class KnowledgeOutputContract(BaseModel):
    extracted_insights: List[KnowledgeInsight] = Field(default_factory=list)
    indexed_documents_count: int = 0
    summary: str
