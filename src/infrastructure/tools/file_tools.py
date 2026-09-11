import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.infrastructure.tools.base import BaseTool, ToolResult
from src.core.logging import logger


class FileTools(BaseTool):
    """File system manipulation tools scoped to a project workspace directory"""

    def __init__(self, workspace_root: str):
        super().__init__("file_tools", "File system operations: read, write, edit, search, and tree traversal")
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Ensure no directory traversal outside workspace root"""
        clean_rel = relative_path.lstrip("/")
        target_path = (self.workspace_root / clean_rel).resolve()
        if not str(target_path).startswith(str(self.workspace_root)):
            raise ValueError(f"Path traversal detected: {relative_path} is outside {self.workspace_root}")
        return target_path

    async def read_file(self, path: str) -> ToolResult:
        start = time.time()
        try:
            target = self._resolve_safe_path(path)
            if not target.exists():
                return ToolResult(
                    tool_name="read_file",
                    success=False,
                    error_message=f"File not found: {path}",
                    execution_time_seconds=time.time() - start,
                )
            content = target.read_text(encoding="utf-8")
            return ToolResult(
                tool_name="read_file",
                success=True,
                data={"path": path, "content": content, "size_bytes": len(content)},
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool_name="read_file",
                success=False,
                error_message=str(e),
                execution_time_seconds=time.time() - start,
            )

    async def write_file(self, path: str, content: str) -> ToolResult:
        start = time.time()
        try:
            target = self._resolve_safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(
                tool_name="write_file",
                success=True,
                data={"path": path, "size_bytes": len(content), "created": True},
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool_name="write_file",
                success=False,
                error_message=str(e),
                execution_time_seconds=time.time() - start,
            )

    async def edit_file(self, path: str, old_text: str, new_text: str) -> ToolResult:
        start = time.time()
        try:
            target = self._resolve_safe_path(path)
            if not target.exists():
                return ToolResult(
                    tool_name="edit_file",
                    success=False,
                    error_message=f"File not found: {path}",
                    execution_time_seconds=time.time() - start,
                )
            content = target.read_text(encoding="utf-8")
            if old_text not in content:
                return ToolResult(
                    tool_name="edit_file",
                    success=False,
                    error_message=f"Pattern to replace was not found in {path}",
                    execution_time_seconds=time.time() - start,
                )
            new_content = content.replace(old_text, new_text, 1)
            target.write_text(new_content, encoding="utf-8")
            return ToolResult(
                tool_name="edit_file",
                success=True,
                data={"path": path, "replaced": True},
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool_name="edit_file",
                success=False,
                error_message=str(e),
                execution_time_seconds=time.time() - start,
            )

    async def analyze_repo(self, subpath: str = "") -> ToolResult:
        start = time.time()
        try:
            target = self._resolve_safe_path(subpath)
            tree = []
            for root, dirs, files in os.walk(target):
                # skip git and venv directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "venv", ".git"]]
                for f in files:
                    if not f.startswith("."):
                        full = Path(root) / f
                        rel = str(full.relative_to(self.workspace_root))
                        tree.append({
                            "path": rel,
                            "size": full.stat().st_size,
                            "extension": full.suffix,
                        })
            return ToolResult(
                tool_name="analyze_repo",
                success=True,
                data={"tree": tree, "total_files": len(tree)},
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool_name="analyze_repo",
                success=False,
                error_message=str(e),
                execution_time_seconds=time.time() - start,
            )
