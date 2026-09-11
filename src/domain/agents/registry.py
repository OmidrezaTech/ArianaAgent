from typing import Dict, Optional, Any
from src.domain.agents.base import BaseAgent
from src.domain.agents.coo import AICooAgent
from src.domain.agents.business_analyst import BusinessAnalystAgent
from src.domain.agents.developer import DeveloperAgent
from src.domain.agents.qa import QAAgent
from src.domain.agents.knowledge import KnowledgeManagerAgent
from src.infrastructure.llm.client import LLMClient
from src.infrastructure.llm.prompts import (
    COO_SYSTEM_PROMPT,
    BA_SYSTEM_PROMPT,
    DEV_SYSTEM_PROMPT,
    QA_SYSTEM_PROMPT,
    KNOWLEDGE_SYSTEM_PROMPT,
)
from src.infrastructure.brain.knowledge_service import KnowledgeService
from src.infrastructure.tools.file_tools import FileTools
from src.infrastructure.tools.git_tools import GitTools
from src.infrastructure.tools.test_tools import TestTools
from src.core.config import settings


class AgentRegistry:
    """Central registry and factory for all 5 Agents"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        brain_service: Optional[KnowledgeService] = None,
        workspace_path: Optional[str] = None,
    ):
        self.llm = llm_client or LLMClient()
        self.brain = brain_service
        self.workspace_path = workspace_path or settings.WORKSPACE_ROOT

        # Instantiate Tools
        self.file_tools = FileTools(self.workspace_path)
        self.git_tools = GitTools(self.workspace_path)
        self.test_tools = TestTools(self.workspace_path)
        self.shared_tools = {
            "file_tools": self.file_tools,
            "git_tools": self.git_tools,
            "test_tools": self.test_tools,
        }

        self._agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        # 1. AI COO
        self._agents["AI_COO"] = AICooAgent(
            agent_id="10000000-0000-0000-0000-000000000001",
            name="AI COO",
            agent_type="AI_COO",
            system_prompt=COO_SYSTEM_PROMPT,
            llm_client=self.llm,
            brain_service=self.brain,
            tools=self.shared_tools,
        )

        # 2. Business Analyst
        self._agents["BUSINESS_ANALYST"] = BusinessAnalystAgent(
            agent_id="10000000-0000-0000-0000-000000000002",
            name="Business Analyst",
            agent_type="BUSINESS_ANALYST",
            system_prompt=BA_SYSTEM_PROMPT,
            llm_client=self.llm,
            brain_service=self.brain,
            tools=self.shared_tools,
        )

        # 3. Developer
        self._agents["DEVELOPER"] = DeveloperAgent(
            agent_id="10000000-0000-0000-0000-000000000003",
            name="Developer",
            agent_type="DEVELOPER",
            system_prompt=DEV_SYSTEM_PROMPT,
            llm_client=self.llm,
            brain_service=self.brain,
            tools=self.shared_tools,
        )

        # 4. QA
        self._agents["QA"] = QAAgent(
            agent_id="10000000-0000-0000-0000-000000000004",
            name="QA Engineer",
            agent_type="QA",
            system_prompt=QA_SYSTEM_PROMPT,
            llm_client=self.llm,
            brain_service=self.brain,
            tools=self.shared_tools,
        )

        # 5. Knowledge Manager
        self._agents["KNOWLEDGE"] = KnowledgeManagerAgent(
            agent_id="10000000-0000-0000-0000-000000000005",
            name="Knowledge Manager",
            agent_type="KNOWLEDGE",
            system_prompt=KNOWLEDGE_SYSTEM_PROMPT,
            llm_client=self.llm,
            brain_service=self.brain,
            tools=self.shared_tools,
        )

    def get_agent(self, agent_type_or_name: str) -> Optional[BaseAgent]:
        key = agent_type_or_name.upper()
        if key in self._agents:
            return self._agents[key]
        for agent in self._agents.values():
            if agent.name.upper() == key:
                return agent
        return None

    def list_agents(self) -> Dict[str, BaseAgent]:
        return self._agents
