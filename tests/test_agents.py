import pytest
from src.domain.agents.registry import AgentRegistry
from src.domain.schemas.agent_contracts import AgentInput


@pytest.mark.asyncio
async def test_agent_registry_initialization():
    registry = AgentRegistry()
    agents = registry.list_agents()
    assert len(agents) == 5
    assert "AI_COO" in agents
    assert "BUSINESS_ANALYST" in agents
    assert "DEVELOPER" in agents
    assert "QA" in agents
    assert "KNOWLEDGE" in agents


@pytest.mark.asyncio
async def test_coo_agent_execution():
    registry = AgentRegistry()
    coo = registry.get_agent("AI_COO")
    assert coo is not None

    agent_input = AgentInput(
        project_id="test-proj-001",
        context={"title": "Create User Service", "description": "Needs registration endpoint"},
    )
    output = await coo.execute(agent_input)
    assert output.status == "SUCCESS"
    assert "workflow_steps" in output.result
    assert len(output.result["workflow_steps"]) > 0


@pytest.mark.asyncio
async def test_ba_agent_execution():
    registry = AgentRegistry()
    ba = registry.get_agent("BUSINESS_ANALYST")
    assert ba is not None

    agent_input = AgentInput(
        project_id="test-proj-001",
        context={"title": "Payment Gateway Integration", "description": "Stripe checkout with webhooks"},
    )
    output = await ba.execute(agent_input)
    assert output.status == "SUCCESS"
    assert "requirements" in output.result
    assert "acceptance_criteria" in output.result


@pytest.mark.asyncio
async def test_dev_agent_execution(tmp_path):
    registry = AgentRegistry(workspace_path=str(tmp_path))
    dev = registry.get_agent("DEVELOPER")
    assert dev is not None

    agent_input = AgentInput(
        project_id="test-proj-001",
        context={"requirements": ["Build item store"], "acceptance_criteria": ["Item must be retrievable"]},
    )
    output = await dev.execute(agent_input)
    assert output.status == "SUCCESS"
    assert "files_created" in output.result
    assert len(output.result["files_created"]) > 0


@pytest.mark.asyncio
async def test_qa_agent_execution(tmp_path):
    registry = AgentRegistry(workspace_path=str(tmp_path))
    qa = registry.get_agent("QA")
    assert qa is not None

    agent_input = AgentInput(
        project_id="test-proj-001",
        context={"requirements": ["Build item store"], "acceptance_criteria": ["Item must be retrievable"]},
    )
    output = await qa.execute(agent_input)
    assert output.status in ["SUCCESS", "REVISE"]
    assert "status" in output.result
