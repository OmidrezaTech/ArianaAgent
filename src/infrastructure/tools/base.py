from typing import Any, Dict, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Dict[str, Any] = {}
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0


class BaseTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
