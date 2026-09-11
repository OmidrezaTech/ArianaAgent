from typing import List, Dict, Any
from src.domain.agents.base import BaseAgent
from src.domain.schemas.agent_contracts import AgentInput, AgentOutput, DevOutputContract
from src.infrastructure.database.models import MemoryType
from src.infrastructure.tools.file_tools import FileTools
from src.infrastructure.tools.git_tools import GitTools
from src.infrastructure.tools.test_tools import TestTools
from src.core.logging import logger


class DeveloperAgent(BaseAgent):
    """Developer Agent: Implements code, creates tests, executes file operations and commits"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        logger.info("dev_agent_executing", project_id=agent_input.project_id)

        requirements = agent_input.context.get("requirements", [])
        acceptance_criteria = agent_input.context.get("acceptance_criteria", [])
        brain_context = await self.get_context(query=str(requirements), project_id=agent_input.project_id)

        file_tool: FileTools = self.tools.get("file_tools")
        git_tool: GitTools = self.tools.get("git_tools")
        test_tool: TestTools = self.tools.get("test_tools")

        repo_structure = {}
        if file_tool:
            analysis_res = await file_tool.analyze_repo()
            if analysis_res.success:
                repo_structure = analysis_res.data

        prompt = f"""
Implement the software solution for the following requirements and acceptance criteria:

Requirements: {requirements}
Acceptance Criteria: {acceptance_criteria}
Existing Repository Files: {repo_structure}
Architecture Guidelines: {brain_context}

Produce the full technical implementation plan, file contents for new files, test suite code, and commit message.
"""

        res = await self.llm.chat(
            prompt=prompt,
            system_prompt=self.system_prompt,
            agent_type="DEVELOPER",
        )

        dev_data = res.parsed_json or {}
        tool_records = []

        # Execute file system operations
        file_contents: Dict[str, str] = dev_data.get("file_contents", {})
        files_created = []
        if file_tool and file_contents:
            for filepath, content in file_contents.items():
                write_res = await file_tool.write_file(filepath, content)
                if write_res.success:
                    files_created.append(filepath)
                tool_records.append({
                    "tool_name": "write_file",
                    "input": {"path": filepath},
                    "output": write_res.data,
                    "status": "SUCCESS" if write_res.success else "FAILED",
                })

        # Run test suite
        test_status = True
        if test_tool:
            test_res = await test_tool.run_tests()
            test_status = test_res.success
            tool_records.append({
                "tool_name": "run_tests",
                "input": {},
                "output": test_res.data,
                "status": "SUCCESS" if test_res.success else "FAILED",
            })

        # Commit changes to Git repository
        commit_hash = "mock-commit-hash"
        if git_tool:
            commit_msg = dev_data.get("commit_message", "feat: implement requested feature")
            commit_res = await git_tool.commit(message=commit_msg, author_name="AI Developer")
            if commit_res.success:
                commit_hash = commit_res.data.get("commit_hash", commit_hash)
            tool_records.append({
                "tool_name": "git_commit",
                "input": {"message": commit_msg},
                "output": commit_res.data,
                "status": "SUCCESS" if commit_res.success else "FAILED",
            })

        dev_data["files_created"] = files_created or dev_data.get("files_created", [])
        dev_data["commit_hash"] = commit_hash
        dev_data["tool_executions"] = tool_records

        await self.save_memory(
            project_id=agent_input.project_id,
            memory_type=MemoryType.PATTERN,
            content=f"Developer authored {len(dev_data['files_created'])} files with commit {commit_hash[:8]}",
            importance=7,
        )

        return AgentOutput(
            status="SUCCESS",
            result=dev_data,
            tokens_used=res.total_tokens,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
            cost=res.cost,
        )
