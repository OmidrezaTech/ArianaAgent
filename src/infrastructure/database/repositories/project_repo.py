from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.infrastructure.database.models import Project, Repository, ProjectMember, UserRole
from src.infrastructure.database.repositories.base_repo import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_with_details(self, project_id: str) -> Optional[Project]:
        result = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.repository),
                selectinload(Project.members),
            )
            .where(Project.id == project_id)
        )
        return result.scalars().first()

    async def list_for_user(self, user_id: str) -> List[Project]:
        result = await self.session.execute(
            select(Project)
            .outerjoin(ProjectMember, Project.id == ProjectMember.project_id)
            .where((Project.created_by == user_id) | (ProjectMember.user_id == user_id))
            .distinct()
        )
        return list(result.scalars().all())

    async def add_member(self, project_id: str, user_id: str, role: UserRole = UserRole.MEMBER) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        return member


class RepositoryRepo(BaseRepository[Repository]):
    def __init__(self, session: AsyncSession):
        super().__init__(Repository, session)

    async def get_by_project(self, project_id: str) -> Optional[Repository]:
        result = await self.session.execute(
            select(Repository).where(Repository.project_id == project_id)
        )
        return result.scalars().first()
