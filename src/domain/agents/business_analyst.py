from src.domain.agents.base import BaseAgent
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput, BAOutputContract
from src.infrastructure.database.models import MemoryType
from src.core.logging import logger


class BusinessAnalystAgent(BaseAgent):
    """Business Analyst Agent: Formulates technical specifications and acceptance criteria"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        logger.info("ba_agent_executing", project_id=agent_input.project_id)

        raw_request = agent_input.context.get("title", "") + "\n" + agent_input.context.get("description", "")
        brain_context = await self.get_context(query=raw_request, project_id=agent_input.project_id)

        prompt = f"""
Transform the following product request into an unambiguous, professional software specification:

Product Request:
{raw_request}

Company Architecture & Domain Guidelines:
{brain_context}

Output Requirements:
- Title and summary
- List of functional requirements with priority (1-5)
- Clear Given-When-Then Acceptance Criteria
- Explicit Business Rules & Constraints
- Task breakdowns
"""

        res = await self.llm.chat(
            prompt=prompt,
            system_prompt=self.system_prompt,
            agent_type="BUSINESS_ANALYST",
        )

        spec_data = res.parsed_json or {}

        await self.save_memory(
            project_id=agent_input.project_id,
            memory_type=MemoryType.LESSON,
            content=f"Business Analyst generated {len(spec_data.get('requirements', []))} requirements and {len(spec_data.get('acceptance_criteria', []))} acceptance criteria.",
            importance=7,
        )

        return AgentOutput(
            status="SUCCESS",
            result=spec_data,
            tokens_used=res.total_tokens,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
            cost=res.cost,
        )
