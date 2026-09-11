from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import User
from src.application.workflow_service import WorkflowService
from src.domain.schemas.workflow_schemas import (
    WorkflowRunCreate,
    WorkflowRunResponse,
    WorkflowResponse,
)
from src.infrastructure.database.repositories.workflow_repo import WorkflowRepository
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    repo = WorkflowRepository(db)
    return await repo.list()


@router.post("/runs", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_workflow_run(
    data: WorkflowRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow_svc = WorkflowService(db)
    run = await workflow_svc.start_workflow_for_request(
        request_id=data.request_id,
        workflow_id=data.workflow_id,
    )
    return run


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(run_id: str, db: AsyncSession = Depends(get_db)):
    workflow_svc = WorkflowService(db)
    return await workflow_svc.get_run_status(run_id)


@router.get("/runs/request/{request_id}", response_model=List[WorkflowRunResponse])
async def list_runs_by_request(request_id: str, db: AsyncSession = Depends(get_db)):
    workflow_svc = WorkflowService(db)
    return await workflow_svc.list_runs_by_request(request_id)
