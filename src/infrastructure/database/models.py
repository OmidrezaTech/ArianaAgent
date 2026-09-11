import enum
import json
import uuid
from datetime import datetime
from typing import List, Optional, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, JSON

from src.infrastructure.database.session import Base
from src.core.config import settings

# ----------------------------------------------------------------------
# Cross-dialect Type Helpers (PostgreSQL & SQLite compatibility)
# ----------------------------------------------------------------------
class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type"""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)


class VectorType(TypeDecorator):
    """Vector type that gracefully falls back to JSON on non-Postgres engines"""
    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 1536):
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dimensions))
            except ImportError:
                return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [float(x) for x in value.strip("[]").split(",") if x]
        return value


JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")

# ----------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------
class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class RequestType(str, enum.Enum):
    FEATURE = "FEATURE"
    BUG = "BUG"
    CHANGE = "CHANGE"
    QUESTION = "QUESTION"
    DOCUMENTATION = "DOCUMENTATION"


class RequestStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskType(str, enum.Enum):
    ANALYSIS = "ANALYSIS"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    BUG_FIX = "BUG_FIX"
    REVIEW = "REVIEW"
    DOCUMENTATION = "DOCUMENTATION"


class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class AgentType(str, enum.Enum):
    AI_COO = "AI_COO"
    BUSINESS_ANALYST = "BUSINESS_ANALYST"
    DEVELOPER = "DEVELOPER"
    QA = "QA"
    KNOWLEDGE = "KNOWLEDGE"


class AgentRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowRunStatus(str, enum.Enum):
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GitProvider(str, enum.Enum):
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    LOCAL = "LOCAL"


class CommitAuthorType(str, enum.Enum):
    HUMAN = "HUMAN"
    AI = "AI"


class BugSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BugStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"


class DocumentType(str, enum.Enum):
    COMPANY_RULE = "COMPANY_RULE"
    CODING_STANDARD = "CODING_STANDARD"
    ARCHITECTURE = "ARCHITECTURE"
    SECURITY_RULE = "SECURITY_RULE"
    SOP = "SOP"
    PROJECT_DOCUMENTATION = "PROJECT_DOCUMENTATION"
    REQUIREMENT = "REQUIREMENT"


class MemoryType(str, enum.Enum):
    LESSON = "LESSON"
    FEEDBACK = "FEEDBACK"
    PATTERN = "PATTERN"
    ERROR = "ERROR"
    PREFERENCE = "PREFERENCE"


class ApprovalType(str, enum.Enum):
    REQUIREMENT_APPROVAL = "REQUIREMENT_APPROVAL"
    CODE_APPROVAL = "CODE_APPROVAL"
    FINAL_APPROVAL = "FINAL_APPROVAL"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ToolStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


# ----------------------------------------------------------------------
# 2. Core Tables
# ----------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), default=UserRole.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    created_projects = relationship("Project", back_populates="creator", foreign_keys="Project.created_by", lazy="selectin")
    created_requests = relationship("Request", back_populates="creator", lazy="selectin")
    project_memberships = relationship("ProjectMember", back_populates="user", lazy="selectin")
    approvals = relationship("Approval", back_populates="requested_from_user", lazy="selectin")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus, native_enum=False), default=ProjectStatus.ACTIVE, nullable=False)
    tech_stack: Mapped[Any] = mapped_column(JSON_TYPE, default=list, nullable=False)
    repository_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_projects", foreign_keys=[created_by], lazy="selectin")
    repository = relationship("Repository", foreign_keys=[repository_id], post_update=True, lazy="selectin")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    requests = relationship("Request", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    workflows = relationship("Workflow", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    decisions = relationship("Decision", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    memories = relationship("Memory", back_populates="project", cascade="all, delete-orphan", lazy="selectin")


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), default=UserRole.MEMBER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members", lazy="selectin")
    user = relationship("User", back_populates="project_memberships", lazy="selectin")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_type: Mapped[RequestType] = mapped_column(Enum(RequestType, native_enum=False), default=RequestType.FEATURE, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus, native_enum=False), default=RequestStatus.NEW, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(SmallInteger, CheckConstraint("priority BETWEEN 1 AND 5"), default=3, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="requests", lazy="selectin")
    creator = relationship("User", back_populates="created_requests", lazy="selectin")
    requirements = relationship("Requirement", back_populates="request", cascade="all, delete-orphan", lazy="selectin")
    tasks = relationship("Task", back_populates="request", cascade="all, delete-orphan", lazy="selectin")
    workflow_runs = relationship("WorkflowRun", back_populates="request", cascade="all, delete-orphan", lazy="selectin")
    approvals = relationship("Approval", back_populates="request", cascade="all, delete-orphan", lazy="selectin")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(GUID(), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_rules: Mapped[Any] = mapped_column(JSON_TYPE, default=list, nullable=False)
    acceptance_criteria: Mapped[Any] = mapped_column(JSON_TYPE, default=list, nullable=False)
    priority: Mapped[int] = mapped_column(SmallInteger, CheckConstraint("priority BETWEEN 1 AND 5"), default=3, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by_agent: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    request = relationship("Request", back_populates="requirements", lazy="selectin")
    agent = relationship("Agent", lazy="selectin")
    tasks = relationship("Task", back_populates="requirement", lazy="selectin")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(GUID(), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True)
    parent_task_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType, native_enum=False), default=TaskType.DEVELOPMENT, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, native_enum=False), default=TaskStatus.TODO, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(SmallInteger, CheckConstraint("priority BETWEEN 1 AND 5"), default=3, nullable=False)
    assigned_agent: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    request = relationship("Request", back_populates="tasks", lazy="selectin")
    requirement = relationship("Requirement", back_populates="tasks", lazy="selectin")
    agent = relationship("Agent", lazy="selectin")
    agent_runs = relationship("AgentRun", back_populates="task", lazy="selectin")
    test_runs = relationship("TestRun", back_populates="task", lazy="selectin")
    bugs = relationship("Bug", back_populates="task", lazy="selectin")


# ----------------------------------------------------------------------
# 3. Agent / Workflow Tables
# ----------------------------------------------------------------------

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[AgentType] = mapped_column(Enum(AgentType, native_enum=False), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    agent_runs = relationship("AgentRun", back_populates="agent", lazy="selectin")
    memories = relationship("Memory", back_populates="agent", cascade="all, delete-orphan", lazy="selectin")


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    definition: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="workflows", lazy="selectin")
    runs = relationship("WorkflowRun", back_populates="workflow", lazy="selectin")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(GUID(), ForeignKey("workflows.id", ondelete="RESTRICT"), nullable=False)
    request_id: Mapped[str] = mapped_column(GUID(), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[WorkflowRunStatus] = mapped_column(Enum(WorkflowRunStatus, native_enum=False), default=WorkflowRunStatus.STARTED, nullable=False, index=True)
    current_step: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="runs", lazy="selectin")
    request = relationship("Request", back_populates="workflow_runs", lazy="selectin")
    agent_runs = relationship("AgentRun", back_populates="workflow_run", cascade="all, delete-orphan", lazy="selectin")
    approvals = relationship("Approval", back_populates="workflow_run", cascade="all, delete-orphan", lazy="selectin")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_run_id: Mapped[str] = mapped_column(GUID(), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[AgentRunStatus] = mapped_column(Enum(AgentRunStatus, native_enum=False), default=AgentRunStatus.PENDING, nullable=False, index=True)
    input_context: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    output: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0.0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="agent_runs", lazy="selectin")
    agent = relationship("Agent", back_populates="agent_runs", lazy="selectin")
    task = relationship("Task", back_populates="agent_runs", lazy="selectin")
    commits = relationship("Commit", back_populates="agent_run", lazy="selectin")
    test_runs = relationship("TestRun", back_populates="agent_run", cascade="all, delete-orphan", lazy="selectin")
    tool_executions = relationship("ToolExecution", back_populates="agent_run", cascade="all, delete-orphan", lazy="selectin")


# ----------------------------------------------------------------------
# 4. Development Tables (Git / QA)
# ----------------------------------------------------------------------

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider: Mapped[GitProvider] = mapped_column(Enum(GitProvider, native_enum=False), default=GitProvider.LOCAL, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id], lazy="selectin")
    branches = relationship("Branch", back_populates="repository", cascade="all, delete-orphan", lazy="selectin")
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan", lazy="selectin")


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("repository_id", "name", name="uq_repo_branch_name"),)

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="branches", lazy="selectin")
    commits = relationship("Commit", back_populates="branch", cascade="all, delete-orphan", lazy="selectin")


class Commit(Base):
    __tablename__ = "commits"
    __table_args__ = (UniqueConstraint("repository_id", "hash", name="uq_repo_commit_hash"),)

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(GUID(), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author_type: Mapped[CommitAuthorType] = mapped_column(Enum(CommitAuthorType, native_enum=False), default=CommitAuthorType.AI, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="commits", lazy="selectin")
    branch = relationship("Branch", back_populates="commits", lazy="selectin")
    agent_run = relationship("AgentRun", back_populates="commits", lazy="selectin")


class TestRun(Base):
    __tablename__ = "test_runs"
    __test__ = False  # Prevent Pytest from collecting ORM class as test suite

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))

    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    agent_run_id: Mapped[str] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("commits.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING", nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    report: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="test_runs", lazy="selectin")
    agent_run = relationship("AgentRun", back_populates="test_runs", lazy="selectin")
    commit = relationship("Commit", lazy="selectin")
    bugs = relationship("Bug", back_populates="test_run", lazy="selectin")


class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    test_run_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("test_runs.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[BugSeverity] = mapped_column(Enum(BugSeverity, native_enum=False), default=BugSeverity.MEDIUM, nullable=False)
    status: Mapped[BugStatus] = mapped_column(Enum(BugStatus, native_enum=False), default=BugStatus.OPEN, nullable=False, index=True)
    detected_by: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="bugs", lazy="selectin")
    test_run = relationship("TestRun", back_populates="bugs", lazy="selectin")
    detector = relationship("Agent", foreign_keys=[detected_by], lazy="selectin")
    assignee = relationship("Agent", foreign_keys=[assigned_to], lazy="selectin")


# ----------------------------------------------------------------------
# 5. Company Brain Tables
# ----------------------------------------------------------------------

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, native_enum=False), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="knowledge_documents", lazy="selectin")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan", lazy="selectin")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),)

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding = mapped_column(VectorType(1536), nullable=True)
    metadata_: Mapped[Any] = mapped_column("metadata", JSON_TYPE, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks", lazy="selectin")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("requests.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_by_type: Mapped[str] = mapped_column(String(20), CheckConstraint("decided_by_type IN ('HUMAN', 'AI')"), nullable=False)
    decided_by_user: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="decisions", lazy="selectin")


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType, native_enum=False), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(SmallInteger, CheckConstraint("importance BETWEEN 1 AND 10"), default=5, nullable=False)
    metadata_: Mapped[Any] = mapped_column("metadata", JSON_TYPE, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="memories", lazy="selectin")
    agent = relationship("Agent", back_populates="memories", lazy="selectin")


# ----------------------------------------------------------------------
# 6. Control Tables
# ----------------------------------------------------------------------

class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    request_id: Mapped[str] = mapped_column(GUID(), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    workflow_run_id: Mapped[str] = mapped_column(GUID(), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    agent_run_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[ApprovalType] = mapped_column(Enum(ApprovalType, native_enum=False), nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus, native_enum=False), default=ApprovalStatus.PENDING, nullable=False, index=True)
    requested_from: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    request = relationship("Request", back_populates="approvals", lazy="selectin")
    workflow_run = relationship("WorkflowRun", back_populates="approvals", lazy="selectin")
    requested_from_user = relationship("User", back_populates="approvals", lazy="selectin")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_run_id: Mapped[str] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    output: Mapped[Any] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    status: Mapped[ToolStatus] = mapped_column(Enum(ToolStatus, native_enum=False), default=ToolStatus.SUCCESS, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    agent_run = relationship("AgentRun", back_populates="tool_executions", lazy="selectin")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_data: Mapped[Optional[Any]] = mapped_column(JSON_TYPE, nullable=True)
    new_data: Mapped[Optional[Any]] = mapped_column(JSON_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
