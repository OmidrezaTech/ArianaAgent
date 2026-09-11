from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from src.infrastructure.database.models import ProjectStatus, GitProvider



class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    git_provider: Optional[GitProvider] = GitProvider.LOCAL
    repo_url: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    tech_stack: Optional[List[str]] = None


class RepositoryResponse(BaseModel):
    id: str
    project_id: str
    provider: GitProvider
    url: Optional[str] = None
    default_branch: str
    local_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    id: str
    status: ProjectStatus
    repository_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    repository: Optional[RepositoryResponse] = None

    model_config = ConfigDict(from_attributes=True)

