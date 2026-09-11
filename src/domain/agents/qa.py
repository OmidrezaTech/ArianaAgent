from src.domain.agents.base import BaseAgent
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput, QAOutputContract
from src.infrastructure.database.models import MemoryType
from src.infrastructure.tools.test_tools import TestTools
from src.core.logging import logger


class QAAgent(BaseAgent):
    """QA Engineer Agent: Validates implementation, executes test runner, verifies acceptance criteria"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        logger.info("qa_agent_executing", project_id=agent_input.project_id)

        requirements = agent_input.context.get("requirements", [])
        acceptance_criteria = agent_input.context.get("acceptance_criteria", [])
        files_created = agent_input.context.get("files_created", [])

        test_tool: TestTools = self.tools.get("test_tools")
        tool_records = []
        test_run_data = {}

        if test_tool:
            test_res = await test_tool.run_tests()
            test_run_data = test_res.data
            tool_records.append({
                "tool_name": "run_tests",
                "input": {},
                "output": test_run_data,
                "status": "SUCCESS" if test_res.success else "FAILED",
            })

        prompt = f"""
Perform formal Quality Assurance evaluation for this implementation:

Requirements: {requirements}
Acceptance Criteria: {acceptance_criteria}
Files Created / Modified: {files_created}
Test Suite Execution Outcome: {test_run_data}

Validate each criterion, determine PASSED or FAILED, and list any defects or regressions found.
"""

        res = await self.llm.chat(
            prompt=prompt,
            system_prompt=self.system_prompt,
            agent_type="QA",
        )

        qa_data = res.parsed_json or {}
        qa_data["tool_executions"] = tool_records
        qa_data["test_run"] = test_run_data

        status_str = qa_data.get("status", "PASSED")
        await self.save_memory(
            project_id=agent_input.project_id,
            memory_type=MemoryType.FEEDBACK,
            content=f"QA evaluated implementation with verdict: {status_str} ({qa_data.get('passed_tests', 0)} passed).",
            importance=8,
        )

        return AgentOutput(
            status="SUCCESS" if status_str == "PASSED" else "REVISE",
            result=qa_data,
            tokens_used=res.total_tokens,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
            cost=res.cost,
        )
