from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db
from src.infrastructure.database.repositories.workflow_repo import AgentRepository
from src.domain.schemas.workflow_schemas import AgentResponse
from src.domain.agents.registry import AgentRegistry

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    repo = AgentRepository(db)
    agents = await repo.list()
    return agents


@router.get("/runtime/active")
async def list_runtime_agents():
    registry = AgentRegistry()
    active_agents = registry.list_agents()
    return {
        key: {
            "name": agent.name,
            "type": agent.agent_type,
            "tools": list(agent.tools.keys()),
        }
        for key, agent in active_agents.items()
    }
