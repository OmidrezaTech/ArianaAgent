import os
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.models import (
    Project,
    Repository,
    Branch,
    UserRole,
    GitProvider,
)
from src.infrastructure.database.repositories.project_repo import (
    ProjectRepository,
    RepositoryRepo,
)
from src.domain.schemas.project_schemas import ProjectCreate, ProjectUpdate
from src.core.exceptions import EntityNotFoundException
from src.core.config import settings


class ProjectService:
    """Handles project lifecycle, workspace scaffolding, and repository bindings"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.repo_repo = RepositoryRepo(session)

    async def create_project(self, data: ProjectCreate, user_id: str) -> Project:
        # Create project entity
        project = Project(
            name=data.name,
            description=data.description,
            tech_stack=data.tech_stack,
            created_by=user_id,
        )
        saved_project = await self.project_repo.create(project)

        # Scaffolding project workspace directory
        proj_dir = Path(settings.WORKSPACE_ROOT) / saved_project.id
        proj_dir.mkdir(parents=True, exist_ok=True)

        # Create attached repository record
        repo = Repository(
            project_id=saved_project.id,
            provider=data.git_provider or GitProvider.LOCAL,
            url=data.repo_url,
            default_branch="main",
            local_path=str(proj_dir),
        )
        saved_repo = await self.repo_repo.create(repo)

        # Create default main branch
        branch = Branch(
            repository_id=saved_repo.id,
            name="main",
            is_default=True,
        )
        self.session.add(branch)

        # Bind repository to project
        saved_project.repository_id = saved_repo.id
        await self.project_repo.update(saved_project)

        # Add creator as owner member
        await self.project_repo.add_member(
            project_id=saved_project.id,
            user_id=user_id,
            role=UserRole.OWNER,
        )

        return saved_project

    async def get_project(self, project_id: str) -> Project:
        project = await self.project_repo.get_with_details(project_id)
        if not project:
            raise EntityNotFoundException("Project", project_id)
        return project

    async def list_projects(self, user_id: str) -> List[Project]:
        return await self.project_repo.list_for_user(user_id)

    async def update_project(self, project_id: str, data: ProjectUpdate) -> Project:
        project = await self.get_project(project_id)
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.status is not None:
            project.status = data.status
        if data.tech_stack is not None:
            project.tech_stack = data.tech_stack
        return await self.project_repo.update(project)
