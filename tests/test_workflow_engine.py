import pytest
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import (
    User,
    Project,
    Request,
    Workflow,
    WorkflowRun,
    WorkflowRunStatus,
    RequestStatus,
    ApprovalStatus,
)
from src.domain.workflows.engine import WorkflowEngine
from src.application.approval_service import ApprovalService
from src.api.main import init_db_and_seed


@pytest.mark.asyncio
async def test_workflow_engine_full_lifecycle():
    await init_db_and_seed()

    async with AsyncSessionLocal() as session:
        # Create Project & Request
        proj = Project(
            name="Test Engine Project",
            created_by="00000000-0000-0000-0000-000000000001",
        )
        session.add(proj)
        await session.flush()

        req = Request(
            project_id=proj.id,
            created_by="00000000-0000-0000-0000-000000000001",
            title="Automated Test Request",
            description="Testing state transitions",
        )
        session.add(req)
        await session.flush()

        wf = Workflow(
            name="Test Fast Pipeline",
            definition={
                "steps": [
                    {"name": "ANALYSIS", "agent": "BUSINESS_ANALYST", "type": "SPECIFICATION"},
                    {"name": "REQUIREMENT_APPROVAL", "agent": "HUMAN", "type": "REQUIREMENT_APPROVAL"},
                    {"name": "DEVELOPMENT", "agent": "DEVELOPER", "type": "IMPLEMENTATION"},
                    {"name": "QA", "agent": "QA", "type": "VERIFICATION"},
                    {"name": "FINAL_APPROVAL", "agent": "HUMAN", "type": "FINAL_APPROVAL"},
                ]
            },
        )
        session.add(wf)
        await session.flush()

        run = WorkflowRun(
            workflow_id=wf.id,
            request_id=req.id,
        )
        session.add(run)
        await session.commit()

        # Execute Engine -> Should pause at REQUIREMENT_APPROVAL
        engine = WorkflowEngine(session)
        paused_run = await engine.execute_run(run.id)
        assert paused_run.status == WorkflowRunStatus.WAITING_APPROVAL
        assert paused_run.current_step == "REQUIREMENT_APPROVAL"

        # Check pending approval
        approval_svc = ApprovalService(session)
        pending = await approval_svc.list_pending_approvals("00000000-0000-0000-0000-000000000001")
        assert len(pending) > 0
        target_app = [a for a in pending if a.workflow_run_id == run.id][0]

        # Human approves requirement
        resumed_run = await approval_svc.process_approval(
            approval_id=target_app.id,
            decision="APPROVED",
            comment="Approved spec",
        )
        assert resumed_run.status == WorkflowRunStatus.WAITING_APPROVAL
        assert resumed_run.current_step == "FINAL_APPROVAL"

        # Final signoff
        pending_final = await approval_svc.list_pending_approvals("00000000-0000-0000-0000-000000000001")
        final_app = [a for a in pending_final if a.workflow_run_id == run.id][0]
        completed_run = await approval_svc.process_approval(
            approval_id=final_app.id,
            decision="APPROVED",
            comment="Ship to production",
        )

        assert completed_run.status == WorkflowRunStatus.COMPLETED
        assert completed_run.completed_at is not None
