from src.domain.agents.base import BaseAgent
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput, COOOutputContract
from src.infrastructure.database.models import MemoryType
from src.core.logging import logger


class AICooAgent(BaseAgent):
    """Chief Operating Officer Agent: Orchestrates workflow, reviews high-level goals, decomposes tasks"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        logger.info("coo_agent_executing", task_id=agent_input.task_id, project_id=agent_input.project_id)
        
        user_request = agent_input.context.get("title", "") + ": " + agent_input.context.get("description", "")
        brain_context = await self.get_context(query=user_request, project_id=agent_input.project_id)

        prompt = f"""
Analyze the following incoming request and construct an optimal execution workflow:

Request: {user_request}
Context / Company Standards: {brain_context}

Provide a structured operational plan with:
1. High-level summary of the requirement
2. Request classification (FEATURE, BUG, REFACTOR, etc.)
3. Priority assessment (1-5)
4. Step-by-step workflow with assigned specialized agents and Human-in-the-Loop gates.
"""

        res = await self.llm.chat(
            prompt=prompt,
            system_prompt=self.system_prompt,
            agent_type="AI_COO",
        )

        plan_data = res.parsed_json or {}
        
        # Save operational memory
        await self.save_memory(
            project_id=agent_input.project_id,
            memory_type=MemoryType.PATTERN,
            content=f"COO planned workflow with {len(plan_data.get('workflow_steps', []))} steps for '{agent_input.context.get('title', 'Request')}'",
            importance=6,
        )

        return AgentOutput(
            status="SUCCESS",
            result=plan_data,
            tokens_used=res.total_tokens,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
            cost=res.cost,
        )
