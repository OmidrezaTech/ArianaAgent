import sys
import os
import pytest

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables for tests to use SQLite so tests run without requiring external Postgres service
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_aicompany.db"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///./test_aicompany.db"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["ENVIRONMENT"] = "test"
