from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import User
from src.application.approval_service import ApprovalService
from src.domain.schemas.approval_schemas import ApprovalAction, ApprovalResponse
from src.domain.schemas.workflow_schemas import WorkflowRunResponse
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


@router.get("/pending", response_model=List[ApprovalResponse])
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApprovalService(db)
    return await service.list_pending_approvals(current_user.id)


@router.post("/{approval_id}/action", response_model=WorkflowRunResponse)
async def act_on_approval(
    approval_id: str,
    action: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApprovalService(db)
    updated_run = await service.process_approval(
        approval_id=approval_id,
        decision=action.status,
        comment=action.comment,
    )
    return updated_run
