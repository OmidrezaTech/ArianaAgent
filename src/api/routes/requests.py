from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import User
from src.application.request_service import RequestService
from src.application.workflow_service import WorkflowService
from src.domain.schemas.request_schemas import (
    RequestCreate,
    RequestUpdate,
    RequestResponse,
)
from src.domain.schemas.workflow_schemas import WorkflowRunResponse
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: RequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_svc = RequestService(db)
    req = await request_svc.create_request(data, user_id=current_user.id)

    # Optionally auto-trigger workflow
    if data.auto_start_workflow:
        workflow_svc = WorkflowService(db)
        await workflow_svc.start_workflow_for_request(req.id)
        # reload request with newly created requirements/tasks
        req = await request_svc.get_request(req.id)

    return req


@router.get("/project/{project_id}", response_model=List[RequestResponse])
async def list_requests_for_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_svc = RequestService(db)
    return await request_svc.list_by_project(project_id)


@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_svc = RequestService(db)
    return await request_svc.get_request(request_id)


@router.patch("/{request_id}", response_model=RequestResponse)
async def update_request(
    request_id: str,
    data: RequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_svc = RequestService(db)
    return await request_svc.update_request(request_id, data)
