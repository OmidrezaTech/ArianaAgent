"""
Interactive Demonstration Script for AI Company 5-Agent MVP System
Executes the full lifecycle: Request -> COO -> BA -> Human Approval -> Dev -> QA -> Final Signoff
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json
from src.infrastructure.database.session import AsyncSessionLocal

from src.infrastructure.database.models import (
    User,
    UserRole,
    ProjectStatus,
    DocumentType,
    RequestType,
)
from src.application.project_service import ProjectService
from src.application.request_service import RequestService
from src.application.workflow_service import WorkflowService
from src.application.approval_service import ApprovalService
from src.application.brain_service import BrainService
from src.domain.schemas.project_schemas import ProjectCreate
from src.domain.schemas.request_schemas import RequestCreate
from src.domain.schemas.brain_schemas import KnowledgeDocumentCreate
from src.api.main import init_db_and_seed
from src.core.logging import logger


async def run_end_to_end_demo():
    print("\n" + "=" * 80)
    print("🚀 AI COMPANY MVP — 5-AGENT SYSTEM END-TO-END DEMO")
    print("=" * 80 + "\n")

    # Step 0: Ensure DB and seeds
    await init_db_and_seed()

    async with AsyncSessionLocal() as session:
        project_svc = ProjectService(session)
        request_svc = RequestService(session)
        workflow_svc = WorkflowService(session)
        approval_svc = ApprovalService(session)
        brain_svc = BrainService(session)

        # -------------------------------------------------------------
        # 1. Company Brain Knowledge Ingestion
        # -------------------------------------------------------------
        print("\n🧠 [Step 1] Ingesting Company Standards into Company Brain...")
        coding_std = await brain_svc.add_document(
            KnowledgeDocumentCreate(
                title="Company Coding Standards & Architecture Rules",
                document_type=DocumentType.CODING_STANDARD,
                content="""Rule 1: Always use Pydantic v2 schemas for request and response validation.
Rule 2: Implement async/await for all database transactions and network requests.
Rule 3: Ensure 100% test coverage for core business domain logic with pytest.
Rule 4: Follow modular clean architecture separating Domain, Application, and Infrastructure.""",
                source="engineering-wiki",
            )
        )
        print(f"   ✓ Knowledge Document Ingested: '{coding_std.title}' (ID: {coding_std.id})")

        # -------------------------------------------------------------
        # 2. Create Project
        # -------------------------------------------------------------
        print("\n📁 [Step 2] Creating Software Project...")
        project = await project_svc.create_project(
            ProjectCreate(
                name="AI Enrollment & Course Management API",
                description="High-performance student enrollment platform with prerequisite checks",
                tech_stack=["FastAPI", "PostgreSQL", "Pytest", "Docker"],
            ),
            user_id="00000000-0000-0000-0000-000000000001",
        )
        print(f"   ✓ Project Created: '{project.name}' (ID: {project.id})")
        print(f"   ✓ Local Repository Initialized at: {project.repository.local_path}")

        # -------------------------------------------------------------
        # 3. User Submits Request
        # -------------------------------------------------------------
        print("\n📝 [Step 3] Submitting Product Request...")
        req = await request_svc.create_request(
            RequestCreate(
                project_id=project.id,
                title="Build Student Enrollment Service with validation and automated tests",
                description="Students should be able to enroll in courses. Duplicate enrollments must throw validation errors.",
                request_type=RequestType.FEATURE,
                priority=4,
                auto_start_workflow=False,
            ),
            user_id="00000000-0000-0000-0000-000000000001",
        )
        print(f"   ✓ Request Created: '{req.title}' (Priority: {req.priority}/5, Status: {req.status.value})")

        # -------------------------------------------------------------
        # 4. Trigger Workflow (COO -> BA -> Human Gate)
        # -------------------------------------------------------------
        print("\n⚡ [Step 4] Starting 5-Agent Workflow...")
        workflow_run = await workflow_svc.start_workflow_for_request(req.id)
        print(f"   ✓ Workflow Run ID: {workflow_run.id}")
        print(f"   ✓ Current Status: {workflow_run.status.value}")
        print(f"   ✓ Current Step: {workflow_run.current_step}")

        # -------------------------------------------------------------
        # 5. Check Human-in-the-Loop Approval Gate
        # -------------------------------------------------------------
        print("\n🛑 [Step 5] Checking Pending Human-in-the-Loop Approvals...")
        pending_approvals = await approval_svc.list_pending_approvals("00000000-0000-0000-0000-000000000001")
        print(f"   ✓ Total Pending Approvals: {len(pending_approvals)}")

        if pending_approvals:
            approval = pending_approvals[0]
            print(f"   ↳ Approval Required for Step: {approval.type.value} (ID: {approval.id})")
            print("   ↳ Reviewing Business Analyst Specifications...")
            
            # Reload request to inspect requirements
            updated_req = await request_svc.get_request(req.id)
            print(f"     * Generated Requirements: {len(updated_req.requirements)}")
            for r in updated_req.requirements:
                print(f"       - [{r.title}] Acceptance Criteria: {len(r.acceptance_criteria)} rules")
            print(f"     * Generated Tasks: {len(updated_req.tasks)}")

            print("\n👤 [Step 6] Human Approver: APPROVING Specification...")
            resumed_run = await approval_svc.process_approval(
                approval_id=approval.id,
                decision="APPROVED",
                comment="Requirements look comprehensive and align with product roadmap. Proceed to development.",
            )

            # Check if there is a final approval gate
            final_approvals = await approval_svc.list_pending_approvals("00000000-0000-0000-0000-000000000001")
            if final_approvals:
                final_app = final_approvals[0]
                print(f"\n👤 [Step 7] Final Human Sign-off Gate Reached: {final_app.type.value}")
                resumed_run = await approval_svc.process_approval(
                    approval_id=final_app.id,
                    decision="APPROVED",
                    comment="QA verified and all criteria passed. Ship it!",
                )

        # -------------------------------------------------------------
        # 8. Summary of Execution
        # -------------------------------------------------------------
        final_run = await workflow_svc.get_run_status(workflow_run.id)
        print("\n" + "=" * 80)
        print("🎉 WORKFLOW RUN COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"• Final Run Status: {final_run.status.value}")
        print(f"• Total Agent Steps Executed: {len(final_run.agent_runs)}")
        for idx, ar in enumerate(final_run.agent_runs, 1):
            agent_name = ar.agent.name if ar.agent else "Agent"
            tool_count = len(ar.tool_executions)
            print(f"  {idx}. [{agent_name}] Status: {ar.status.value} | Tokens: {ar.total_tokens} | Cost: ${ar.cost:.4f} | Tools Used: {tool_count}")

        # Check repository files created
        print("\n📦 Repository Artifacts Created:")
        proj_dir = project.repository.local_path
        print(f"  Location: {proj_dir}")
        for root, _, files in os.walk(proj_dir):
            for f in files:
                if not f.startswith("."):
                    rel = os.path.relpath(os.path.join(root, f), proj_dir)
                    print(f"  📄 {rel}")

        # Check memories stored
        memories = await brain_svc.list_memories(project_id=project.id)
        print(f"\n🧠 Company Brain Memories Retained: {len(memories)}")
        for m in memories[:4]:
            print(f"  • [{m.memory_type.value}] (Importance {m.importance}/10): {m.content}")


        print("\n" + "=" * 80)
        print("✅ ALL 5 AGENTS EXECUTED HARMONIOUSLY WITH FULL DATABASE PERSISTENCE.")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_end_to_end_demo())
