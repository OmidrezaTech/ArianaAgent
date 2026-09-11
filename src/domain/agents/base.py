from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput
from src.infrastructure.llm.client import LLMClient
from src.infrastructure.brain.knowledge_service import KnowledgeService
from src.infrastructure.database.models import MemoryType
from src.core.logging import logger


class BaseAgent(ABC):
    """Abstract Base Class for all 5 Agents in the MVP System"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
        system_prompt: str,
        llm_client: LLMClient,
        brain_service: Optional[KnowledgeService] = None,
        tools: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.llm = llm_client
        self.brain = brain_service
        self.tools = tools or {}

    @abstractmethod
    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Executes the specific agent's cognitive and tool loop"""
        pass

    async def get_context(self, query: str, project_id: str) -> List[str]:
        """Retrieve relevant context chunks from the Company Brain"""
        if not self.brain:
            return []
        chunks = await self.brain.search_context(query=query, project_id=project_id, top_k=3)
        return [c["content"] for c in chunks]

    async def save_memory(
        self,
        project_id: str,
        memory_type: MemoryType,
        content: str,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Save actionable insights and lessons learned into the agent's memory"""
        if self.brain:
            await self.brain.save_memory(
                project_id=project_id,
                agent_id=self.agent_id,
                memory_type=memory_type,
                content=content,
                importance=importance,
                metadata=metadata or {},
            )
            logger.info("agent_memory_saved", agent=self.name, memory_type=memory_type.value)
