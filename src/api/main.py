from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.core.logging import configure_logging, logger
from src.core.exceptions import AICompanyException
from src.infrastructure.database.session import async_engine, Base, AsyncSessionLocal
from src.infrastructure.database.models import User, UserRole, Agent, AgentType, Workflow
from src.api.dependencies import hash_password
from src.api.routes import (
    auth,
    projects,
    requests,
    workflows,
    approvals,
    agents,
    brain,
    health,
)

configure_logging()



async def init_db_and_seed():
    """Create all tables and seed default agents / workflow on system startup"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Seed Owner User
        owner = await session.get(User, "00000000-0000-0000-0000-000000000001")
        if not owner:
            owner = User(
                id="00000000-0000-0000-0000-000000000001",
                email="owner@company.ai",
                password_hash=hash_password("owner123"),
                full_name="Company Owner",
                role=UserRole.OWNER,
            )
            session.add(owner)

        # 2. Seed 5 Agents (Powered by Google Gemini)
        seed_agents = [
            (
                "10000000-0000-0000-0000-000000000001",
                "AI COO",
                AgentType.AI_COO,
                "Operational brain that orchestrates all other agents",
                "gemini-1.5-pro",
                {"max_tokens": 4096, "temperature": 0.3},
            ),
            (
                "10000000-0000-0000-0000-000000000002",
                "Business Analyst",
                AgentType.BUSINESS_ANALYST,
                "Transforms raw requests into structured specifications",
                "gemini-1.5-pro",
                {"max_tokens": 4096, "temperature": 0.2},
            ),
            (
                "10000000-0000-0000-0000-000000000003",
                "Developer",
                AgentType.DEVELOPER,
                "Implements code based on specifications",
                "gemini-1.5-pro",
                {"max_tokens": 8192, "temperature": 0.1, "tools": ["read_file", "write_file", "edit_file", "run_tests"]},
            ),
            (
                "10000000-0000-0000-0000-000000000004",
                "QA Engineer",
                AgentType.QA,
                "Validates implementation against requirements",
                "gemini-1.5-pro",
                {"max_tokens": 4096, "temperature": 0.1},
            ),
            (
                "10000000-0000-0000-0000-000000000005",
                "Knowledge Manager",
                AgentType.KNOWLEDGE,
                "Manages Company Brain: documents, memories, decisions",
                "gemini-1.5-flash",
                {"max_tokens": 2048, "temperature": 0.2},
            ),
        ]


        for ag_id, name, ag_type, desc, model, cfg in seed_agents:
            existing_agent = await session.get(Agent, ag_id)
            if not existing_agent:
                ag = Agent(
                    id=ag_id,
                    name=name,
                    type=ag_type,
                    description=desc,
                    model=model,
                    system_prompt=f"You are the {name} of the AI Company.",
                    config=cfg,
                )
                session.add(ag)

        # 3. Seed Default Workflow
        existing_wf = await session.get(Workflow, "20000000-0000-0000-0000-000000000001")
        if not existing_wf:
            wf = Workflow(
                id="20000000-0000-0000-0000-000000000001",
                name="Software Development Workflow",
                description="End-to-end flow from request to production",
                version=1,
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
            session.add(wf)


        await session.commit()
        logger.info("database_and_seed_initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", app_name=settings.PROJECT_NAME, version=settings.VERSION)
    await init_db_and_seed()
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade 5-Agent Autonomous Software Organization MVP with Clean Architecture and pgvector",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(AICompanyException)
async def ai_company_exception_handler(request: Request, exc: AICompanyException):
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "message": exc.message, "details": exc.details},
    )


# Include Routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(requests.router, prefix=settings.API_V1_STR)
app.include_router(workflows.router, prefix=settings.API_V1_STR)
app.include_router(approvals.router, prefix=settings.API_V1_STR)
app.include_router(agents.router, prefix=settings.API_V1_STR)
app.include_router(brain.router, prefix=settings.API_V1_STR)

# Serve Frontend SPA
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    @app.get("/dashboard", response_class=HTMLResponse)
    async def serve_dashboard():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>AI Company Dashboard</h1>")

