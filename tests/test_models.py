import uuid
import pytest
from src.infrastructure.database.models import (

    User,
    Project,
    Request,
    Requirement,
    Task,
    Agent,
    Workflow,
    WorkflowRun,
    AgentRun,
    Repository,
    Branch,
    Commit,
    TestRun,
    Bug,
    KnowledgeDocument,
    KnowledgeChunk,
    Decision,
    Memory,
    Approval,
    ToolExecution,
    AuditLog,
    UserRole,
    ProjectStatus,
    RequestType,
    AgentType,
)
from src.infrastructure.database.session import AsyncSessionLocal, Base, async_engine


@pytest.mark.asyncio
async def test_create_all_22_tables_and_relations():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. User
        user = User(
            email=f"test_engineer_{uuid.uuid4().hex[:8]}@company.ai",
            password_hash="hash123",
            full_name="Test Engineer",
            role=UserRole.ADMIN,
        )

        session.add(user)
        await session.flush()
        assert user.id is not None

        # 2. Project
        project = Project(
            name="Autonomous Microservice",
            description="Built by AI Agents",
            created_by=user.id,
        )
        session.add(project)
        await session.flush()
        assert project.id is not None

        # 3. Agent
        agent = Agent(
            name=f"Test QA Agent {uuid.uuid4().hex[:6]}",
            type=AgentType.QA,
            model="gpt-4o",
        )
        session.add(agent)
        await session.flush()
        assert agent.id is not None


        # 4. Request
        req = Request(
            project_id=project.id,
            created_by=user.id,
            title="Implement OAuth2 Authentication",
            request_type=RequestType.FEATURE,
            priority=5,
        )
        session.add(req)
        await session.flush()
        assert req.id is not None

        # 5. Requirement
        requirement = Requirement(
            project_id=project.id,
            request_id=req.id,
            title="JWT token generation",
            created_by_agent=agent.id,
        )
        session.add(requirement)
        await session.flush()
        assert requirement.id is not None

        # 6. Task
        task = Task(
            project_id=project.id,
            request_id=req.id,
            requirement_id=requirement.id,
            title="Write Auth handler",
            assigned_agent=agent.id,
        )
        session.add(task)
        await session.flush()
        assert task.id is not None

        # 7. Workflow & WorkflowRun
        wf = Workflow(
            name="Fast Delivery Flow",
            definition={"steps": []},
        )
        session.add(wf)
        await session.flush()

        w_run = WorkflowRun(
            workflow_id=wf.id,
            request_id=req.id,
        )
        session.add(w_run)
        await session.flush()

        # 8. AgentRun
        a_run = AgentRun(
            workflow_run_id=w_run.id,
            agent_id=agent.id,
            model="gpt-4o",
        )
        session.add(a_run)
        await session.flush()

        # 9. Repository, Branch, Commit
        repo = Repository(
            project_id=project.id,
            default_branch="main",
        )
        session.add(repo)
        await session.flush()

        branch = Branch(
            repository_id=repo.id,
            name="feature/auth",
        )
        session.add(branch)
        await session.flush()

        commit = Commit(
            repository_id=repo.id,
            branch_id=branch.id,
            agent_run_id=a_run.id,
            hash="c0ffee123456",
            message="feat: JWT token logic",
        )
        session.add(commit)
        await session.flush()

        # 10. TestRun & Bug
        t_run = TestRun(
            project_id=project.id,
            agent_run_id=a_run.id,
            commit_id=commit.id,
            total_tests=5,
            passed_tests=5,
        )
        session.add(t_run)
        await session.flush()

        bug = Bug(
            project_id=project.id,
            test_run_id=t_run.id,
            title="Minor header typo",
            detected_by=agent.id,
        )
        session.add(bug)
        await session.flush()

        # 11. KnowledgeDoc & Chunk
        doc = KnowledgeDocument(
            title="Auth Standards",
            document_type="SECURITY_RULE",
            content="Use RS256 with 2048-bit keys",
        )
        session.add(doc)
        await session.flush()

        chunk = KnowledgeChunk(
            document_id=doc.id,
            content="Use RS256 with 2048-bit keys",
            chunk_index=0,
            embedding=[0.1] * 1536,
        )
        session.add(chunk)
        await session.flush()

        # 12. Decision & Memory
        decision = Decision(
            project_id=project.id,
            title="Adopt JWT over Session Cookies",
            decision="Stateless JWT with short expiration",
            decided_by_type="HUMAN",
            decided_by_user=user.id,
        )
        session.add(decision)
        await session.flush()

        memory = Memory(
            project_id=project.id,
            agent_id=agent.id,
            memory_type="LESSON",
            content="Token rotation prevents replay attacks",
            importance=9,
        )
        session.add(memory)
        await session.flush()

        # 13. Approval, ToolExecution, AuditLog
        approval = Approval(
            project_id=project.id,
            request_id=req.id,
            workflow_run_id=w_run.id,
            type="REQUIREMENT_APPROVAL",
            requested_from=user.id,
        )
        session.add(approval)
        await session.flush()

        t_exec = ToolExecution(
            agent_run_id=a_run.id,
            tool_name="pytest_runner",
            input={"path": "tests"},
            output={"passed": 5},
        )
        session.add(t_exec)
        await session.flush()

        audit = AuditLog(
            user_id=user.id,
            project_id=project.id,
            entity_type="Request",
            entity_id=req.id,
            action="CREATED",
        )
        session.add(audit)
        await session.flush()

        await session.commit()
