# 📘 AI Company Architecture & System Design

## 🏛️ Clean Architecture & Modular Monolith

```text
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│  REST Routers → Pydantic Schemas → JWT/Auth Context      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Application Layer (Use Cases)               │
│  ProjectService, RequestService, WorkflowService,        │
│  ApprovalService, BrainService                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Domain Layer (Core Logic)                │
│  5 Agents (COO, BA, Dev, QA, Knowledge), Registry,       │
│  Workflow Engine, State Machine, Pydantic Contracts      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Infrastructure Layer (External)             │
│  Database (SQLAlchemy 2.0 + pgvector), LLM Client,       │
│  Tool Layer (File, Git, Pytest), Company Brain (RAG)     │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 The 5 Autonomous Agents

| Agent | Role | Model | Primary Tools & Capabilities |
|---|---|---|---|
| **AI COO** | Operational brain & Orchestration | `gpt-4o` | Request deconstruction, dynamic workflow synthesis, risk & complexity assessment |
| **Business Analyst** | Specification & Product Engineering | `gpt-4o` | Functional requirements extraction, Given-When-Then acceptance criteria, business rules |
| **Developer** | Full-Stack Implementation | `claude-sonnet-4-5` | Safe workspace file operations (`write_file`, `edit_file`), Git commit generation, test authoring |
| **QA Engineer** | Quality & Verification | `gpt-4o` | Automated pytest execution, coverage calculation, acceptance criteria checking, bug filing |
| **Knowledge Manager** | Company Brain & Memory Curation | `gpt-4o-mini` | RAG vector search (`pgvector` 1536 dims), pattern extraction, episodic & semantic memory retention |

---

## 🔁 Complete Workflow Execution Lifecycle

```text
1. User Submits Feature / Bug Request (POST /api/requests)
   ↓
2. AI COO Analyzes Request & Builds Execution Plan
   ↓
3. Business Analyst Produces Formal Specification & Acceptance Criteria
   ↓
4. 🛑 Human-in-the-Loop Approval Gate: REQUIREMENT_APPROVAL
   ↓ (User calls POST /api/approvals/{id}/action -> APPROVED)
5. Developer Agent Authors Code & Pytest Test Suites in Sandboxed Workspace
   ↓
6. QA Engineer Executes Test Runner & Verifies All Criteria
   ↓
7. If QA Fails → FIX_LOOP (Developer repairs defects)
   ↓
8. 🛑 Human-in-the-Loop Approval Gate: FINAL_APPROVAL
   ↓ (User calls POST /api/approvals/{id}/action -> APPROVED)
9. Knowledge Manager Extracts Lessons & Indexes into Company Brain
   ↓
10. Workflow Run Reaches COMPLETED Status
```
