from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.models import Request, RequestStatus
from src.infrastructure.database.repositories.request_repo import RequestRepository
from src.infrastructure.database.repositories.workflow_repo import WorkflowRepository
from src.domain.schemas.request_schemas import RequestCreate, RequestUpdate
from src.core.exceptions import EntityNotFoundException


class RequestService:
    """Manages incoming feature and bug requests"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.request_repo = RequestRepository(session)
        self.workflow_repo = WorkflowRepository(session)

    async def create_request(self, data: RequestCreate, user_id: str) -> Request:
        req = Request(
            project_id=data.project_id,
            created_by=user_id,
            title=data.title,
            description=data.description,
            request_type=data.request_type,
            status=RequestStatus.NEW,
            priority=data.priority,
        )
        saved_req = await self.request_repo.create(req)
        return saved_req

    async def get_request(self, request_id: str) -> Request:
        self.session.expire_all()
        req = await self.request_repo.get_with_relations(request_id)
        if not req:
            raise EntityNotFoundException("Request", request_id)
        return req


    async def list_by_project(self, project_id: str) -> List[Request]:
        return await self.request_repo.list_by_project(project_id)

    async def update_request(self, request_id: str, data: RequestUpdate) -> Request:
        req = await self.get_request(request_id)
        if data.title is not None:
            req.title = data.title
        if data.description is not None:
            req.description = data.description
        if data.status is not None:
            req.status = data.status
        if data.priority is not None:
            req.priority = data.priority
        return await self.request_repo.update(req)
