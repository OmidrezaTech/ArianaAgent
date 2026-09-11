from src.domain.agents.base import BaseAgent
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput, KnowledgeOutputContract
from src.infrastructure.database.models import MemoryType
from src.core.logging import logger


class KnowledgeManagerAgent(BaseAgent):
    """Knowledge Manager Agent: Curates company memory, indexes standards, synthesizes insights"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        logger.info("knowledge_agent_executing", project_id=agent_input.project_id)

        workflow_summary = agent_input.context.get("workflow_summary", "")

        prompt = f"""
Review the completed engineering workflow and extract key architectural lessons, reusable patterns, and system memories:

Workflow Summary:
{workflow_summary}

Synthesize findings into structured KnowledgeInsight records.
"""

        res = await self.llm.chat(
            prompt=prompt,
            system_prompt=self.system_prompt,
            agent_type="KNOWLEDGE",
        )

        output_data = res.parsed_json or {}

        # Save extracted insights directly into memory
        for insight in output_data.get("extracted_insights", []):
            cat = insight.get("category", "PATTERN")
            mem_type = MemoryType.PATTERN if cat == "PATTERN" else MemoryType.LESSON
            await self.save_memory(
                project_id=agent_input.project_id,
                memory_type=mem_type,
                content=insight.get("content", ""),
                importance=insight.get("importance", 5),
            )

        return AgentOutput(
            status="SUCCESS",
            result=output_data,
            tokens_used=res.total_tokens,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
            cost=res.cost,
        )
