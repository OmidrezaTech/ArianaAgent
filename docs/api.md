# 🌐 API Reference — AI Company MVP

Base URL: `http://localhost:8000/api`

## 1. Authentication (`/api/auth`)
- `POST /api/auth/register`: Register new user (`email`, `password`, `full_name`, `role`).
- `POST /api/auth/login`: Authenticate and receive bearer token.
- `GET /api/auth/me`: Get current authenticated user details.

## 2. Projects (`/api/projects`)
- `POST /api/projects`: Create software project and initialize Git repository.
- `GET /api/projects`: List all accessible projects.
- `GET /api/projects/{id}`: Get project details with linked repository and members.
- `PATCH /api/projects/{id}`: Update project metadata or status.

## 3. Requests (`/api/requests`)
- `POST /api/requests`: Submit new feature/bug request (`title`, `description`, `request_type`, `priority`, `auto_start_workflow`).
- `GET /api/requests/project/{project_id}`: List all requests for a project.
- `GET /api/requests/{id}`: Get request details, requirements, and tasks.

## 4. Workflows (`/api/workflows`)
- `GET /api/workflows`: List active workflow definitions.
- `POST /api/workflows/runs`: Start workflow run for a request.
- `GET /api/workflows/runs/{id}`: Inspect run status, current step, agent steps, token metrics, and cost.
- `GET /api/workflows/runs/request/{request_id}`: List workflow runs for a request.

## 5. Human Approvals (`/api/approvals`)
- `GET /api/approvals/pending`: List pending approval gates assigned to current user.
- `POST /api/approvals/{id}/action`: Approve (`APPROVED`) or Reject (`REJECTED`) with optional comment. Resumes workflow execution automatically.

## 6. Agents (`/api/agents`)
- `GET /api/agents`: List configured agents in database.
- `GET /api/agents/runtime/active`: Inspect runtime active agent instances and their toolbindings.

## 7. Company Brain (`/api/brain`)
- `POST /api/brain/documents`: Ingest knowledge document (rules, standards, architecture) with vector chunking.
- `GET /api/brain/search?query=...`: Semantic cosine similarity vector search over ingested knowledge.
- `POST /api/brain/decisions`: Log semantic decision with reasoning.
- `GET /api/brain/memories?project_id=...`: Retrieve episodic & semantic lessons learned by agents.

## 8. Health & System (`/health`)
- `GET /health`: Healthcheck, system uptime, and provider status.
