from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.infrastructure.database.models import (
    Workflow,
    WorkflowRun,
    AgentRun,
    Agent,
    ToolExecution,
    AuditLog,
)
from src.infrastructure.database.repositories.base_repo import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    def __init__(self, session: AsyncSession):
        super().__init__(Workflow, session)

    async def get_default_workflow(self) -> Optional[Workflow]:
        result = await self.session.execute(
            select(Workflow).where(Workflow.is_active == True).limit(1)
        )
        return result.scalars().first()


class WorkflowRunRepository(BaseRepository[WorkflowRun]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkflowRun, session)

    async def get_with_details(self, run_id: str) -> Optional[WorkflowRun]:
        result = await self.session.execute(
            select(WorkflowRun)
            .options(
                selectinload(WorkflowRun.agent_runs).selectinload(AgentRun.tool_executions),
                selectinload(WorkflowRun.agent_runs).selectinload(AgentRun.agent),
                selectinload(WorkflowRun.approvals),
                selectinload(WorkflowRun.workflow),
                selectinload(WorkflowRun.request),
            )
            .where(WorkflowRun.id == run_id)
        )
        return result.scalars().first()

    async def list_by_request(self, request_id: str) -> List[WorkflowRun]:
        result = await self.session.execute(
            select(WorkflowRun)
            .options(
                selectinload(WorkflowRun.agent_runs).selectinload(AgentRun.tool_executions),
                selectinload(WorkflowRun.approvals),
            )
            .where(WorkflowRun.request_id == request_id)
            .order_by(WorkflowRun.started_at.desc())
        )
        return list(result.scalars().all())


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession):
        super().__init__(Agent, session)

    async def get_by_name(self, name: str) -> Optional[Agent]:
        result = await self.session.execute(
            select(Agent).where(Agent.name == name)
        )
        return result.scalars().first()

    async def get_by_type(self, agent_type: str) -> Optional[Agent]:
        result = await self.session.execute(
            select(Agent).where(Agent.type == agent_type)
        )
        return result.scalars().first()


class AgentRunRepository(BaseRepository[AgentRun]):
    def __init__(self, session: AsyncSession):
        super().__init__(AgentRun, session)

    async def get_with_tools(self, agent_run_id: str) -> Optional[AgentRun]:
        result = await self.session.execute(
            select(AgentRun)
            .options(selectinload(AgentRun.tool_executions))
            .where(AgentRun.id == agent_run_id)
        )
        return result.scalars().first()


class ToolExecutionRepository(BaseRepository[ToolExecution]):
    def __init__(self, session: AsyncSession):
        super().__init__(ToolExecution, session)


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
