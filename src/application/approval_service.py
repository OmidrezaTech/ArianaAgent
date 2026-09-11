from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import (
    Approval,
    ApprovalStatus,
    WorkflowRun,
    WorkflowRunStatus,
    RequestStatus,
)
from src.infrastructure.database.repositories.approval_repo import ApprovalRepository
from src.infrastructure.database.repositories.workflow_repo import WorkflowRunRepository
from src.infrastructure.database.repositories.request_repo import RequestRepository
from src.domain.workflows.engine import WorkflowEngine
from src.core.exceptions import EntityNotFoundException, WorkflowExecutionException
from src.core.logging import logger


class ApprovalService:
    """Manages Human-in-the-Loop approval gates and workflow resumption"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.approval_repo = ApprovalRepository(session)
        self.workflow_run_repo = WorkflowRunRepository(session)
        self.request_repo = RequestRepository(session)
        self.engine = WorkflowEngine(session)

    async def list_pending_approvals(self, user_id: str) -> List[Approval]:
        return await self.approval_repo.list_pending_by_user(user_id)

    async def process_approval(
        self,
        approval_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        comment: Optional[str] = None,
    ) -> WorkflowRun:
        approval = await self.approval_repo.get_by_id(approval_id)
        if not approval:
            raise EntityNotFoundException("Approval", approval_id)

        approval.status = ApprovalStatus.APPROVED if decision == "APPROVED" else ApprovalStatus.REJECTED
        approval.comment = comment
        approval.resolved_at = datetime.now(timezone.utc)
        await self.approval_repo.update(approval)
        await self.session.commit()


        run = await self.workflow_run_repo.get_with_details(approval.workflow_run_id)
        if not run:
            raise EntityNotFoundException("WorkflowRun", approval.workflow_run_id)

        if decision == "APPROVED":
            logger.info("human_approved_resuming_workflow", approval_id=approval.id, run_id=run.id)
            # Resume workflow from next step
            resumed_run = await self.engine.execute_run(
                workflow_run_id=run.id,
                resume_from_approval=True,
            )
            return resumed_run
        else:
            logger.info("human_rejected_halting_workflow", approval_id=approval.id, run_id=run.id)
            run.status = WorkflowRunStatus.CANCELLED
            run.error_message = f"Rejected by human: {comment or 'No comment provided'}"
            if run.request:
                run.request.status = RequestStatus.CANCELLED
            await self.workflow_run_repo.update(run)
            await self.session.commit()
            return run

