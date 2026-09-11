import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app, init_db_and_seed


@pytest.mark.asyncio
async def test_frontend_dashboard_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "AI Company" in res.text
        assert "سیستم ارکستراسیون ۵ Agent" in res.text

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
async def test_projects_crud_api():
    await init_db_and_seed()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Project
        res = await ac.post(
            "/api/projects",
            json={
                "name": "API Test Project",
                "description": "Integration test",
                "tech_stack": ["FastAPI", "PostgreSQL"],
            },
        )
        assert res.status_code == 201
        proj = res.json()
        proj_id = proj["id"]
        assert proj["name"] == "API Test Project"

        # List Projects
        res = await ac.get("/api/projects")
        assert res.status_code == 200
        assert len(res.json()) > 0

        # Get Project
        res = await ac.get(f"/api/projects/{proj_id}")
        assert res.status_code == 200
        assert res.json()["id"] == proj_id


@pytest.mark.asyncio
async def test_request_and_workflow_api():
    await init_db_and_seed()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create project
        proj_res = await ac.post(
            "/api/projects",
            json={"name": "Pipeline Project", "tech_stack": ["Python"]},
        )
        proj_id = proj_res.json()["id"]

        # 2. Create Request (auto_start_workflow=False)
        req_res = await ac.post(
            "/api/requests",
            json={
                "project_id": proj_id,
                "title": "Build notification service",
                "description": "Send webhook events",
                "auto_start_workflow": False,
            },
        )
        assert req_res.status_code == 201
        req_id = req_res.json()["id"]

        # 3. Start Workflow
        run_res = await ac.post(
            "/api/workflows/runs",
            json={"request_id": req_id},
        )
        assert run_res.status_code == 201
        run_data = run_res.json()
        assert run_data["status"] == "WAITING_APPROVAL"


@pytest.mark.asyncio
async def test_brain_api():
    await init_db_and_seed()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Ingest document
        doc_res = await ac.post(
            "/api/brain/documents",
            json={
                "title": "API Rate Limiting Policy",
                "document_type": "COMPANY_RULE",
                "content": "All public endpoints must have a rate limit of 100 requests per minute.",
            },
        )
        assert doc_res.status_code == 201

        # 2. Search Brain
        search_res = await ac.get("/api/brain/search?query=rate+limiting")
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) > 0
