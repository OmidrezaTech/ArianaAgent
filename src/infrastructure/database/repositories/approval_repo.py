from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.infrastructure.database.models import Approval, ApprovalStatus
from src.infrastructure.database.repositories.base_repo import BaseRepository


class ApprovalRepository(BaseRepository[Approval]):
    def __init__(self, session: AsyncSession):
        super().__init__(Approval, session)

    async def list_pending_by_user(self, user_id: str) -> List[Approval]:
        result = await self.session.execute(
            select(Approval)
            .where(
                Approval.requested_from == user_id,
                Approval.status == ApprovalStatus.PENDING,
            )
            .order_by(Approval.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_workflow_run(self, workflow_run_id: str) -> List[Approval]:
        result = await self.session.execute(
            select(Approval)
            .where(Approval.workflow_run_id == workflow_run_id)
            .order_by(Approval.created_at.asc())
        )
        return list(result.scalars().all())
