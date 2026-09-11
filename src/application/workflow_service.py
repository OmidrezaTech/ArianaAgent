from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.models import (
    Workflow,
    WorkflowRun,
    WorkflowRunStatus,
    Request,
)
from src.infrastructure.database.repositories.workflow_repo import (
    WorkflowRepository,
    WorkflowRunRepository,
)
from src.infrastructure.database.repositories.request_repo import RequestRepository
from src.domain.workflows.engine import WorkflowEngine
from src.domain.agents.registry import AgentRegistry
from src.core.exceptions import EntityNotFoundException


class WorkflowService:
    """Coordinates workflow lifecycle and triggers the execution engine"""

    def __init__(self, session: AsyncSession, agent_registry: Optional[AgentRegistry] = None):
        self.session = session
        self.workflow_repo = WorkflowRepository(session)
        self.workflow_run_repo = WorkflowRunRepository(session)
        self.request_repo = RequestRepository(session)
        self.engine = WorkflowEngine(session, agent_registry=agent_registry)

    async def start_workflow_for_request(
        self, request_id: str, workflow_id: Optional[str] = None
    ) -> WorkflowRun:
        request = await self.request_repo.get_by_id(request_id)
        if not request:
            raise EntityNotFoundException("Request", request_id)

        # Retrieve specified workflow or default global workflow
        if workflow_id:
            wf = await self.workflow_repo.get_by_id(workflow_id)
        else:
            wf = await self.workflow_repo.get_default_workflow()

        if not wf:
            # Create default baseline workflow if none exists in database
            wf = Workflow(
                name="Standard Software Delivery Workflow",
                description="End-to-end multi-agent pipeline",
                definition={
                    "steps": [
                        {"name": "ANALYSIS", "agent": "BUSINESS_ANALYST", "type": "SPECIFICATION"},
                        {"name": "REQUIREMENT_APPROVAL", "agent": "HUMAN", "type": "REQUIREMENT_APPROVAL"},
                        {"name": "DEVELOPMENT", "agent": "DEVELOPER", "type": "IMPLEMENTATION"},
                        {"name": "QA", "agent": "QA", "type": "VERIFICATION"},
                        {"name": "FIX_LOOP", "agent": "DEVELOPER", "type": "BUG_FIX", "condition": "qa_failed"},
                        {"name": "FINAL_APPROVAL", "agent": "HUMAN", "type": "FINAL_APPROVAL"},
                        {"name": "KNOWLEDGE_CURATION", "agent": "KNOWLEDGE", "type": "BRAIN_RETENTION"},
                    ]
                },
            )
            wf = await self.workflow_repo.create(wf)


        run = WorkflowRun(
            workflow_id=wf.id,
            request_id=request.id,
            status=WorkflowRunStatus.STARTED,
        )
        saved_run = await self.workflow_run_repo.create(run)

        # Execute the workflow engine
        executed_run = await self.engine.execute_run(saved_run.id)
        return executed_run

    async def get_run_status(self, run_id: str) -> WorkflowRun:
        self.session.expire_all()
        run = await self.workflow_run_repo.get_with_details(run_id)
        if not run:
            raise EntityNotFoundException("WorkflowRun", run_id)
        return run


    async def list_runs_by_request(self, request_id: str) -> List[WorkflowRun]:
        return await self.workflow_run_repo.list_by_request(request_id)
