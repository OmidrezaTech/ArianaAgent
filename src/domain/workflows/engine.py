import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from src.infrastructure.database.models import (
    WorkflowRun,
    WorkflowRunStatus,
    AgentRun,
    AgentRunStatus,
    Approval,
    ApprovalStatus,
    ApprovalType,
    ToolExecution,
    ToolStatus,
    Requirement,
    Task,
    TaskType,
    TaskStatus,
    Request,
    RequestStatus,
    Commit,
    TestRun,
    Bug,
    CommitAuthorType,
)
from src.infrastructure.database.repositories.workflow_repo import (
    WorkflowRunRepository,
    AgentRunRepository,
    ToolExecutionRepository,
)
from src.infrastructure.database.repositories.request_repo import (
    RequestRepository,
    RequirementRepository,
    TaskRepository,
    CommitRepository,
    TestRunRepository,
    BugRepository,
)
from src.infrastructure.database.repositories.approval_repo import ApprovalRepository
from src.domain.agents.registry import AgentRegistry
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput
from src.core.exceptions import WorkflowExecutionException
from src.core.logging import logger


class WorkflowEngine:
    """Orchestrates end-to-end multi-agent workflow runs with state persistence and human approval gates"""

    def __init__(
        self,
        session: AsyncSession,
        agent_registry: Optional[AgentRegistry] = None,
    ):
        self.session = session
        self.workflow_run_repo = WorkflowRunRepository(session)
        self.agent_run_repo = AgentRunRepository(session)
        self.tool_exec_repo = ToolExecutionRepository(session)
        self.request_repo = RequestRepository(session)
        self.requirement_repo = RequirementRepository(session)
        self.task_repo = TaskRepository(session)
        self.approval_repo = ApprovalRepository(session)
        self.commit_repo = CommitRepository(session)
        self.test_run_repo = TestRunRepository(session)
        self.bug_repo = BugRepository(session)
        self.agent_registry = agent_registry or AgentRegistry()

    async def execute_run(
        self,
        workflow_run_id: str,
        resume_from_approval: bool = False,
    ) -> WorkflowRun:
        run = await self.workflow_run_repo.get_with_details(workflow_run_id)
        if not run:
            raise WorkflowExecutionException(f"WorkflowRun {workflow_run_id} not found")

        request = run.request
        definition = run.workflow.definition or {}
        steps: List[Dict[str, Any]] = definition.get("steps", [])

        # Configure Agent Registry with Brain Service and Project-specific Workspace Path
        from src.infrastructure.brain.knowledge_service import KnowledgeService
        from pathlib import Path
        from src.core.config import settings
        project_workspace = str(Path(settings.WORKSPACE_ROOT) / request.project_id)
        brain_svc = KnowledgeService(self.session)
        self.agent_registry = AgentRegistry(
            brain_service=brain_svc,
            workspace_path=project_workspace,
        )


        if not steps:
            # Fallback default steps
            steps = [
                {"name": "ANALYSIS", "agent": "BUSINESS_ANALYST", "type": "SPECIFICATION"},
                {"name": "REQUIREMENT_APPROVAL", "agent": "HUMAN", "type": "REQUIREMENT_APPROVAL"},
                {"name": "DEVELOPMENT", "agent": "DEVELOPER", "type": "IMPLEMENTATION"},
                {"name": "QA", "agent": "QA", "type": "VERIFICATION"},
                {"name": "FINAL_APPROVAL", "agent": "HUMAN", "type": "FINAL_APPROVAL"},
            ]

        run.status = WorkflowRunStatus.IN_PROGRESS
        request.status = RequestStatus.IN_PROGRESS
        await self.session.flush()

        logger.info("workflow_run_started", run_id=run.id, total_steps=len(steps))

        # Workflow execution context accumulator
        context_accumulator: Dict[str, Any] = {
            "title": request.title,
            "description": request.description or "",
            "project_id": request.project_id,
            "request_id": request.id,
            "workflow_run_id": run.id,
            "requirements": [],
            "acceptance_criteria": [],
            "files_created": [],
            "qa_status": "PASSED",
        }

        # Determine starting index if resuming
        start_idx = 0
        if resume_from_approval and run.current_step:
            for idx, step in enumerate(steps):
                if step.get("name") == run.current_step:
                    start_idx = idx + 1
                    break

        for step_idx in range(start_idx, len(steps)):
            step = steps[step_idx]
            step_name = step.get("name")
            agent_type = step.get("agent")
            step_type = step.get("type", "GENERAL")
            condition = step.get("condition")

            # Check skip condition (e.g., FIX_LOOP only if qa_failed)
            if condition == "qa_failed" and context_accumulator.get("qa_status") == "PASSED":
                logger.info("skipping_conditional_step", step=step_name, condition=condition)
                continue

            run.current_step = step_name
            await self.session.flush()

            # Handle Human Gate
            if agent_type == "HUMAN":
                logger.info("human_approval_gate_reached", step=step_name, run_id=run.id)
                approval_type = ApprovalType.FINAL_APPROVAL if "FINAL" in step_type else ApprovalType.REQUIREMENT_APPROVAL
                
                # Create Approval Record
                approval = Approval(
                    project_id=request.project_id,
                    request_id=request.id,
                    workflow_run_id=run.id,
                    type=approval_type,
                    status=ApprovalStatus.PENDING,
                    requested_from=request.created_by,
                )
                await self.approval_repo.create(approval)

                run.status = WorkflowRunStatus.WAITING_APPROVAL
                request.status = RequestStatus.REVIEW
                await self.session.commit()
                return run


            # Agent Execution
            agent = self.agent_registry.get_agent(agent_type)
            if not agent:
                raise WorkflowExecutionException(f"Agent {agent_type} not registered in AgentRegistry")

            agent_run = AgentRun(
                workflow_run_id=run.id,
                agent_id=agent.agent_id,
                status=AgentRunStatus.RUNNING,
                input_context=context_accumulator,
                model="gpt-4o",
            )
            await self.agent_run_repo.create(agent_run)

            agent_input = AgentInput(
                project_id=request.project_id,
                request_id=request.id,
                workflow_run_id=run.id,
                context=context_accumulator,
            )

            try:
                output: AgentOutput = await agent.execute(agent_input)

                agent_run.status = AgentRunStatus.COMPLETED
                agent_run.output = output.result
                agent_run.prompt_tokens = output.prompt_tokens
                agent_run.completion_tokens = output.completion_tokens
                agent_run.total_tokens = output.tokens_used
                agent_run.cost = output.cost
                agent_run.completed_at = datetime.now(timezone.utc)


                # Process Agent Specific Side-Effects
                await self._process_agent_side_effects(
                    agent_type=agent_type,
                    output=output.result,
                    agent_run=agent_run,
                    request=request,
                    context_accumulator=context_accumulator,
                )

                await self.session.flush()

            except Exception as e:
                agent_run.status = AgentRunStatus.FAILED
                agent_run.error_message = str(e)
                run.status = WorkflowRunStatus.FAILED
                run.error_message = f"Step {step_name} failed: {str(e)}"
                request.status = RequestStatus.FAILED
                await self.session.flush()
                raise WorkflowExecutionException(f"Execution failed at step {step_name}: {str(e)}")

        # Workflow complete
        run.status = WorkflowRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        request.status = RequestStatus.COMPLETED
        await self.session.commit()


        logger.info("workflow_run_completed_successfully", run_id=run.id)
        return run


    async def _process_agent_side_effects(
        self,
        agent_type: str,
        output: Dict[str, Any],
        agent_run: AgentRun,
        request: Request,
        context_accumulator: Dict[str, Any],
    ):
        """Creates appropriate database entities (Requirements, Tasks, Commits, TestRuns, ToolExecutions)"""
        
        # 1. Record Tool Executions
        for tool_rec in output.get("tool_executions", []):
            t_exec = ToolExecution(
                agent_run_id=agent_run.id,
                tool_name=tool_rec.get("tool_name", "generic_tool"),
                input=tool_rec.get("input", {}),
                output=tool_rec.get("output", {}),
                status=ToolStatus.SUCCESS if tool_rec.get("status") == "SUCCESS" else ToolStatus.FAILED,
            )
            await self.tool_exec_repo.create(t_exec)

        # 2. Business Analyst -> Persist Requirements & Tasks
        if agent_type == "BUSINESS_ANALYST":
            req_items = output.get("requirements", [])
            for r_item in req_items:
                req_entity = Requirement(
                    project_id=request.project_id,
                    request_id=request.id,
                    title=r_item.get("title", "Requirement"),
                    description=r_item.get("description"),
                    business_rules=r_item.get("business_rules", []),
                    acceptance_criteria=r_item.get("acceptance_criteria", []),
                    priority=r_item.get("priority", 3),
                    status="APPROVED",
                    created_by_agent=agent_run.agent_id,
                )
                saved_req = await self.requirement_repo.create(req_entity)

            # Create tasks
            for task_title in output.get("tasks", []):
                t = Task(
                    project_id=request.project_id,
                    request_id=request.id,
                    title=task_title,
                    task_type=TaskType.DEVELOPMENT,
                    status=TaskStatus.TODO,
                    priority=request.priority,
                    assigned_agent="10000000-0000-0000-0000-000000000003",
                )
                await self.task_repo.create(t)

            context_accumulator["requirements"] = req_items
            context_accumulator["acceptance_criteria"] = output.get("acceptance_criteria", [])

        # 3. Developer -> Persist Git Commits
        elif agent_type == "DEVELOPER":
            commit_hash = output.get("commit_hash")
            if commit_hash and request.project and request.project.repository_id:
                c = Commit(
                    repository_id=request.project.repository_id,
                    branch_id=request.project.repository.branches[0].id if request.project.repository.branches else "00000000-0000-0000-0000-000000000001",
                    agent_run_id=agent_run.id,
                    hash=commit_hash,
                    message=output.get("commit_message", "Implement features"),
                    author_type=CommitAuthorType.AI,
                )
                # Attempt to save commit if repo exists
                try:
                    await self.commit_repo.create(c)
                except Exception:
                    pass

            context_accumulator["files_created"] = output.get("files_created", [])

        # 4. QA -> Persist TestRuns & Bugs
        elif agent_type == "QA":
            context_accumulator["qa_status"] = output.get("status", "PASSED")
            test_run_data = output.get("test_run", {})
            
            test_run_entity = TestRun(
                project_id=request.project_id,
                agent_run_id=agent_run.id,
                status="COMPLETED",
                total_tests=output.get("total_tests", 1),
                passed_tests=output.get("passed_tests", 1),
                failed_tests=output.get("failed_tests", 0),
                coverage=output.get("coverage_percentage", 100.0),
                report=test_run_data,
                completed_at=datetime.now(timezone.utc),
            )

            await self.test_run_repo.create(test_run_entity)

            # Persist bugs if any
            for b in output.get("bugs", []):
                bug_entity = Bug(
                    project_id=request.project_id,
                    test_run_id=test_run_entity.id,
                    title=b.get("title", "Defect"),
                    description=b.get("description"),
                    severity=b.get("severity", "MEDIUM"),
                    status="OPEN",
                    detected_by=agent_run.agent_id,
                )
                await self.bug_repo.create(bug_entity)
