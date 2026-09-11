from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.infrastructure.database.models import (
    Request,
    Requirement,
    Task,
    TestRun,
    Bug,
    Commit,
    Branch,
)
from src.infrastructure.database.repositories.base_repo import BaseRepository


class RequestRepository(BaseRepository[Request]):
    def __init__(self, session: AsyncSession):
        super().__init__(Request, session)

    async def get_with_relations(self, request_id: str) -> Optional[Request]:
        result = await self.session.execute(
            select(Request)
            .options(
                selectinload(Request.requirements),
                selectinload(Request.tasks),
                selectinload(Request.workflow_runs),
                selectinload(Request.approvals),
            )
            .where(Request.id == request_id)
        )
        return result.scalars().first()

    async def list_by_project(self, project_id: str) -> List[Request]:
        result = await self.session.execute(
            select(Request)
            .options(
                selectinload(Request.requirements),
                selectinload(Request.tasks),
            )
            .where(Request.project_id == project_id)
            .order_by(Request.created_at.desc())
        )
        return list(result.scalars().all())


class RequirementRepository(BaseRepository[Requirement]):
    def __init__(self, session: AsyncSession):
        super().__init__(Requirement, session)

    async def list_by_request(self, request_id: str) -> List[Requirement]:
        result = await self.session.execute(
            select(Requirement).where(Requirement.request_id == request_id)
        )
        return list(result.scalars().all())


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def list_by_request(self, request_id: str) -> List[Task]:
        result = await self.session.execute(
            select(Task).where(Task.request_id == request_id)
        )
        return list(result.scalars().all())


class TestRunRepository(BaseRepository[TestRun]):
    def __init__(self, session: AsyncSession):
        super().__init__(TestRun, session)


class BugRepository(BaseRepository[Bug]):
    def __init__(self, session: AsyncSession):
        super().__init__(Bug, session)

    async def list_open_by_project(self, project_id: str) -> List[Bug]:
        result = await self.session.execute(
            select(Bug).where(
                Bug.project_id == project_id,
                Bug.status.in_(["OPEN", "IN_PROGRESS", "REOPENED"])
            )
        )
        return list(result.scalars().all())


class CommitRepository(BaseRepository[Commit]):
    def __init__(self, session: AsyncSession):
        super().__init__(Commit, session)


class BranchRepository(BaseRepository[Branch]):
    def __init__(self, session: AsyncSession):
        super().__init__(Branch, session)
