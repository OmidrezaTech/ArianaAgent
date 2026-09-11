# 🚀 AI Company MVP — 5-Agent Autonomous Software Organization

A production-grade, modular monolith AI organization framework built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL 15+ with pgvector**, and **Pydantic v2**.

---

## 🌟 Core Features

- **22 PostgreSQL Tables in 6 Groups**: Complete schema with strict foreign keys, indexes, triggers, and native `pgvector` embedding storage (1536 dims).
- **5 Specialized Autonomous Agents**:
  1. `AI COO`: Operational orchestrator & workflow planner
  2. `Business Analyst`: Requirement engineer & acceptance criteria synthesizer
  3. `Developer`: Code author, git committer, test builder
  4. `QA Engineer`: Automated test executor, coverage verifier, bug reporter
  5. `Knowledge Manager`: Company Brain curator & memory synthesizer
- **Workflow Engine & State Machine**:
  - Asynchronous step execution
  - **Human-in-the-Loop gates** (`REQUIREMENT_APPROVAL`, `FINAL_APPROVAL`)
  - Automated defect repair loops (`FIX_LOOP` triggered on QA failures)
  - Token tracking, execution timing, and cost calculation per step
- **Company Brain (RAG + Memory + Decisions)**:
  - Vector cosine similarity search (`pgvector` / in-memory fallback)
  - Episodic & semantic agent memories with importance rating
  - Structured architectural decision records (ADRs)
- **Tool Sandbox**:
  - `FileTools`: Sandboxed workspace read, write, edit, and tree analysis
  - `GitTools`: Automated commit, branch, diff, and repository management
  - `TestTools`: Pytest execution and coverage calculation
- **Multi-Provider LLM Abstraction**:
  - OpenAI API (`gpt-4o`, `text-embedding-3-small`)
  - Anthropic API (`claude-sonnet-4-5`)
  - Deterministic high-fidelity local simulator for offline development & testing

---

## 📁 Project Structure

```text
├── pyproject.toml              # Python project metadata & dependencies
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # PostgreSQL (pgvector) + Redis + API
├── .env.example                # Environment variables template
├── scripts/
│   ├── init_postgres.sql       # Pure PostgreSQL DDL & seeds
│   ├── setup_db.py             # Database table creation & seed loader
│   └── run_demo.py             # Interactive end-to-end multi-agent execution demo
├── src/
│   ├── core/                   # Config, logging, domain exceptions
│   ├── domain/
│   │   ├── schemas/            # Pydantic v2 validation contracts
│   │   ├── agents/             # 5 Agent implementations & Registry
│   │   └── workflows/          # Orchestration engine & state machine
│   ├── infrastructure/
│   │   ├── database/           # 22 SQLAlchemy 2.0 models & repositories
│   │   ├── llm/                # LLM client & structured prompt templates
│   │   ├── tools/              # File, Git, and Pytest tools
│   │   └── brain/              # Vector search, RAG, and memory service
│   ├── application/            # Business use cases & facades
│   └── api/                    # FastAPI routers, middleware, dependencies
└── tests/                      # Full pytest test suite
```

---

## ⚡ Quick Start

### 1. Installation
```bash
# Clone the repository and install dependencies
pip install -e .
```

### 2. Run Interactive End-to-End Demo
Run the complete 5-agent pipeline demonstrating knowledge ingestion, project creation, request planning, human approval gating, code generation, automated testing, and final signoff:

```bash
python3 scripts/run_demo.py
```

### 3. Run Test Suite
```bash
pytest -v
```

### 4. Start the FastAPI API Server
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at: `http://localhost:8000/docs`

---

## 🐳 Running with Docker Compose (PostgreSQL + pgvector)

```bash
docker-compose up --build
```
This launches:
- **PostgreSQL 16 with pgvector extension** on port `5432` with all 22 tables preloaded from `scripts/init_postgres.sql`.
- **Redis 7** on port `6379`.
- **FastAPI Application** on port `8000`.

---

## 📊 Database Schema (22 Tables)

| Group | Tables |
|---|---|
| **Core** | `users`, `projects`, `project_members`, `requests`, `requirements`, `tasks` |
| **Agent / Workflow** | `agents`, `workflows`, `workflow_runs`, `agent_runs` |
| **Development** | `repositories`, `branches`, `commits`, `test_runs`, `bugs` |
| **Company Brain** | `knowledge_documents`, `knowledge_chunks` (vector 1536), `decisions`, `memories` |
| **Control** | `approvals`, `tool_executions`, `audit_logs` |
| **Extensions** | `pgvector`, `uuid-ossp`, `pgcrypto` |
