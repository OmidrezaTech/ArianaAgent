from typing import Any, Optional


class AICompanyException(Exception):
    """Base exception for AI Company system"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class EntityNotFoundException(AICompanyException):
    """Raised when an entity is not found in database"""
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(f"{entity_name} with ID '{entity_id}' not found.")
        self.entity_name = entity_name
        self.entity_id = entity_id


class WorkflowExecutionException(AICompanyException):
    """Raised when workflow execution encounters a fatal error"""
    pass


class AgentExecutionException(AICompanyException):
    """Raised when agent reasoning or tool execution fails"""
    def __init__(self, agent_name: str, message: str, details: Optional[Any] = None):
        super().__init__(f"Agent [{agent_name}] execution failed: {message}", details)
        self.agent_name = agent_name


class ApprovalRequiredException(AICompanyException):
    """Raised when human approval blocks automated progression"""
    def __init__(self, approval_id: str, message: str = "Human approval required"):
        super().__init__(message)
        self.approval_id = approval_id


class ToolExecutionException(AICompanyException):
    """Raised when a specific tool fails during execution"""
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Tool [{tool_name}] failed: {message}")
        self.tool_name = tool_name


class LLMClientException(AICompanyException):
    """Raised when LLM API request fails"""
    pass
