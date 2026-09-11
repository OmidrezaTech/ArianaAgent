-- =====================================================================
-- 📘 طراحی کامل دیتابیس MVP — سیستم ۵ Agent
-- PostgreSQL 15+ with pgvector
-- =====================================================================

-- 0. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. ENUM Types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('OWNER', 'ADMIN', 'MEMBER');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE project_status AS ENUM ('ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE request_type AS ENUM ('FEATURE', 'BUG', 'CHANGE', 'QUESTION', 'DOCUMENTATION');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE request_status AS ENUM (
        'NEW', 'ANALYZING', 'PLANNED', 'IN_PROGRESS',
        'REVIEW', 'COMPLETED', 'FAILED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE task_type AS ENUM (
        'ANALYSIS', 'DEVELOPMENT', 'TEST', 'BUG_FIX', 'REVIEW', 'DOCUMENTATION'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE task_status AS ENUM (
        'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE', 'BLOCKED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE agent_type AS ENUM (
        'AI_COO', 'BUSINESS_ANALYST', 'DEVELOPER', 'QA', 'KNOWLEDGE'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE agent_run_status AS ENUM (
        'PENDING', 'RUNNING', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE workflow_run_status AS ENUM (
        'STARTED', 'IN_PROGRESS', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE git_provider AS ENUM ('GITHUB', 'GITLAB', 'LOCAL');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE commit_author_type AS ENUM ('HUMAN', 'AI');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bug_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bug_status AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'REOPENED', 'CLOSED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE document_type AS ENUM (
        'COMPANY_RULE', 'CODING_STANDARD', 'ARCHITECTURE',
        'SECURITY_RULE', 'SOP', 'PROJECT_DOCUMENTATION', 'REQUIREMENT'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE memory_type AS ENUM ('LESSON', 'FEEDBACK', 'PATTERN', 'ERROR', 'PREFERENCE');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE approval_type AS ENUM ('REQUIREMENT_APPROVAL', 'CODE_APPROVAL', 'FINAL_APPROVAL');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE approval_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE tool_status AS ENUM ('SUCCESS', 'FAILED', 'TIMEOUT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 2. Core Tables
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            user_role NOT NULL DEFAULT 'MEMBER',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    status          project_status NOT NULL DEFAULT 'ACTIVE',
    tech_stack      JSONB NOT NULL DEFAULT '[]'::jsonb,
    repository_id   UUID,
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_members (
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        user_role NOT NULL DEFAULT 'MEMBER',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    request_type    request_type NOT NULL DEFAULT 'FEATURE',
    status          request_status NOT NULL DEFAULT 'NEW',
    priority        SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS requirements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    request_id          UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    business_rules      JSONB NOT NULL DEFAULT '[]'::jsonb,
    acceptance_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    priority            SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    status              VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    version             INTEGER NOT NULL DEFAULT 1,
    created_by_agent    UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    request_id      UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    requirement_id  UUID REFERENCES requirements(id) ON DELETE SET NULL,
    parent_task_id  UUID REFERENCES tasks(id) ON DELETE SET NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    task_type       task_type NOT NULL DEFAULT 'DEVELOPMENT',
    status          task_status NOT NULL DEFAULT 'TODO',
    priority        SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    assigned_agent  UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Agent / Workflow Tables
CREATE TABLE IF NOT EXISTS agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    type            agent_type NOT NULL,
    description     TEXT,
    model           VARCHAR(100) NOT NULL,
    system_prompt   TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    config          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add agent FKs
DO $$ BEGIN
    ALTER TABLE requirements
        ADD CONSTRAINT fk_requirements_agent
        FOREIGN KEY (created_by_agent) REFERENCES agents(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    ALTER TABLE tasks
        ADD CONSTRAINT fk_tasks_agent
        FOREIGN KEY (assigned_agent) REFERENCES agents(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS workflows (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES projects(id) ON DELETE CASCADE,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    version     INTEGER NOT NULL DEFAULT 1,
    definition  JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id     UUID NOT NULL REFERENCES workflows(id) ON DELETE RESTRICT,
    request_id      UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    status          workflow_run_status NOT NULL DEFAULT 'STARTED',
    current_step    VARCHAR(50),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id   UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    agent_id          UUID NOT NULL REFERENCES agents(id) ON DELETE RESTRICT,
    task_id           UUID REFERENCES tasks(id) ON DELETE SET NULL,
    status            agent_run_status NOT NULL DEFAULT 'PENDING',
    input_context     JSONB NOT NULL DEFAULT '{}'::jsonb,
    output            JSONB NOT NULL DEFAULT '{}'::jsonb,
    model             VARCHAR(100) NOT NULL,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    cost              NUMERIC(10, 6) NOT NULL DEFAULT 0,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,
    error_message     TEXT
);

-- 4. Development Tables
CREATE TABLE IF NOT EXISTS repositories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    provider        git_provider NOT NULL DEFAULT 'LOCAL',
    url             TEXT,
    default_branch  VARCHAR(100) NOT NULL DEFAULT 'main',
    local_path      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    ALTER TABLE projects
        ADD CONSTRAINT fk_projects_repository
        FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, name)
);

CREATE TABLE IF NOT EXISTS commits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    branch_id       UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    agent_run_id    UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    hash            VARCHAR(64) NOT NULL,
    message         TEXT NOT NULL,
    author_type     commit_author_type NOT NULL DEFAULT 'AI',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, hash)
);

CREATE TABLE IF NOT EXISTS test_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id         UUID REFERENCES tasks(id) ON DELETE SET NULL,
    agent_run_id    UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    commit_id       UUID REFERENCES commits(id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    total_tests     INTEGER NOT NULL DEFAULT 0,
    passed_tests    INTEGER NOT NULL DEFAULT 0,
    failed_tests    INTEGER NOT NULL DEFAULT 0,
    coverage        NUMERIC(5, 2),
    report          JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bugs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id         UUID REFERENCES tasks(id) ON DELETE SET NULL,
    test_run_id     UUID REFERENCES test_runs(id) ON DELETE SET NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    severity        bug_severity NOT NULL DEFAULT 'MEDIUM',
    status          bug_status NOT NULL DEFAULT 'OPEN',
    detected_by     UUID REFERENCES agents(id) ON DELETE SET NULL,
    assigned_to     UUID REFERENCES agents(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- 5. Company Brain Tables
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    document_type   document_type NOT NULL,
    content         TEXT NOT NULL,
    source          VARCHAR(255),
    version         INTEGER NOT NULL DEFAULT 1,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    embedding       vector(1536),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS decisions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    request_id        UUID REFERENCES requests(id) ON DELETE SET NULL,
    title             VARCHAR(255) NOT NULL,
    decision          TEXT NOT NULL,
    reason            TEXT,
    decided_by_type   VARCHAR(20) NOT NULL CHECK (decided_by_type IN ('HUMAN', 'AI')),
    decided_by_user   UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_run_id      UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    agent_id        UUID REFERENCES agents(id) ON DELETE CASCADE,
    memory_type     memory_type NOT NULL,
    content         TEXT NOT NULL,
    importance      SMALLINT NOT NULL DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

-- 6. Control Tables
CREATE TABLE IF NOT EXISTS approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    request_id      UUID REFERENCES requests(id) ON DELETE CASCADE,
    workflow_run_id UUID REFERENCES workflow_runs(id) ON DELETE CASCADE,
    agent_run_id    UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    type            approval_type NOT NULL,
    status          approval_status NOT NULL DEFAULT 'PENDING',
    requested_from  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    comment         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id    UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_name       VARCHAR(100) NOT NULL,
    input           JSONB NOT NULL DEFAULT '{}'::jsonb,
    output          JSONB NOT NULL DEFAULT '{}'::jsonb,
    status          tool_status NOT NULL DEFAULT 'SUCCESS',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    entity_type     VARCHAR(50) NOT NULL,
    entity_id       UUID NOT NULL,
    action          VARCHAR(50) NOT NULL,
    old_data        JSONB,
    new_data        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Indexes
CREATE INDEX IF NOT EXISTS idx_requests_project_status ON requests(project_id, status);
CREATE INDEX IF NOT EXISTS idx_requests_created_by     ON requests(created_by);
CREATE INDEX IF NOT EXISTS idx_requirements_request    ON requirements(request_id);
CREATE INDEX IF NOT EXISTS idx_requirements_project    ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status    ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_parent            ON tasks(parent_task_id) WHERE parent_task_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent    ON tasks(assigned_agent);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_request   ON workflow_runs(request_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status    ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_workflow     ON agent_runs(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent        ON agent_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status       ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_started      ON agent_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_commits_repo            ON commits(repository_id);
CREATE INDEX IF NOT EXISTS idx_commits_branch          ON commits(branch_id);
CREATE INDEX IF NOT EXISTS idx_commits_agent_run       ON commits(agent_run_id) WHERE agent_run_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_test_runs_project       ON test_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_agent_run     ON test_runs(agent_run_id);
CREATE INDEX IF NOT EXISTS idx_bugs_project_status     ON bugs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_bugs_assigned           ON bugs(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_project  ON knowledge_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc    ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_vec    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_decisions_project       ON decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_project_agent  ON memories(project_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status_user   ON approvals(status, requested_from);
CREATE INDEX IF NOT EXISTS idx_tool_exec_agent_run     ON tool_executions(agent_run_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity       ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created      ON audit_logs(created_at DESC);

-- 8. Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated ON users;
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_projects_updated ON projects;
CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_requests_updated ON requests;
CREATE TRIGGER trg_requests_updated BEFORE UPDATE ON requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_requirements_updated ON requirements;
CREATE TRIGGER trg_requirements_updated BEFORE UPDATE ON requirements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_tasks_updated ON tasks;
CREATE TRIGGER trg_tasks_updated BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_agents_updated ON agents;
CREATE TRIGGER trg_agents_updated BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_workflows_updated ON workflows;
CREATE TRIGGER trg_workflows_updated BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_repositories_updated ON repositories;
CREATE TRIGGER trg_repositories_updated BEFORE UPDATE ON repositories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_knowledge_docs_upd ON knowledge_documents;
CREATE TRIGGER trg_knowledge_docs_upd BEFORE UPDATE ON knowledge_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 9. Seed Data
INSERT INTO users (id, email, password_hash, full_name, role) VALUES
('00000000-0000-0000-0000-000000000001', 'owner@company.ai', '$2b$12$placeholder', 'Company Owner', 'OWNER')
ON CONFLICT (id) DO NOTHING;

INSERT INTO agents (id, name, type, description, model, system_prompt, config) VALUES
('10000000-0000-0000-0000-000000000001', 'AI COO', 'AI_COO',
 'Operational brain that orchestrates all other agents',
 'gemini-1.5-pro', 'You are the COO of an AI-driven company. Orchestrate workflows, decompose tasks, and manage agent assignments with maximum clarity.',
 '{"max_tokens": 4096, "temperature": 0.3}'::jsonb),

('10000000-0000-0000-0000-000000000002', 'Business Analyst', 'BUSINESS_ANALYST',
 'Transforms raw requests into structured specifications',
 'gemini-1.5-pro', 'You are a senior business analyst. Transform raw product requests into actionable specifications with strict acceptance criteria and business rules.',
 '{"max_tokens": 4096, "temperature": 0.2}'::jsonb),

('10000000-0000-0000-0000-000000000003', 'Developer', 'DEVELOPER',
 'Implements code based on specifications',
 'gemini-1.5-pro', 'You are a senior software engineer. Write clean, production-grade code following software engineering best practices.',
 '{"max_tokens": 8192, "temperature": 0.1, "tools": ["read_file","write_file","edit_file","run_tests"]}'::jsonb),

('10000000-0000-0000-0000-000000000004', 'QA Engineer', 'QA',
 'Validates implementation against requirements',
 'gemini-1.5-pro', 'You are a QA engineer. Validate implementation against requirements, execute tests, calculate coverage, and catch edge-case bugs.',
 '{"max_tokens": 4096, "temperature": 0.1}'::jsonb),

('10000000-0000-0000-0000-000000000005', 'Knowledge Manager', 'KNOWLEDGE',
 'Manages Company Brain: documents, memories, decisions',
 'gemini-1.5-flash', 'You manage company knowledge, indexing documentation, surfacing patterns, and retrieving semantic context for team workflows.',
 '{"max_tokens": 2048, "temperature": 0.2}'::jsonb)
ON CONFLICT (id) DO UPDATE SET model = EXCLUDED.model;


INSERT INTO workflows (id, name, description, version, definition) VALUES
('20000000-0000-0000-0000-000000000001',
 'Software Development Workflow',
 'End-to-end flow from request to production',
 1,
 '{
   "steps": [
     {"name": "ANALYSIS",             "agent": "BUSINESS_ANALYST", "type": "SPECIFICATION"},
     {"name": "REQUIREMENT_APPROVAL", "agent": "HUMAN",            "type": "REQUIREMENT_APPROVAL"},
     {"name": "DEVELOPMENT",          "agent": "DEVELOPER",        "type": "IMPLEMENTATION"},
     {"name": "QA",                   "agent": "QA",               "type": "VERIFICATION"},
     {"name": "FIX_LOOP",             "agent": "DEVELOPER",        "type": "BUG_FIX", "condition": "qa_failed"},
     {"name": "FINAL_APPROVAL",       "agent": "HUMAN",            "type": "FINAL_APPROVAL"},
     {"name": "KNOWLEDGE_CURATION",   "agent": "KNOWLEDGE",        "type": "BRAIN_RETENTION"}
   ]
 }'::jsonb)
ON CONFLICT (id) DO NOTHING;

