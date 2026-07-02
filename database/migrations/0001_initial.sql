-- SmartCoat Release 1.4 initial PostgreSQL schema
-- Knowledge Capture MVP scaffold

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS knowledge_objects (
    object_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    owner TEXT,
    lifecycle_state TEXT NOT NULL DEFAULT 'draft',
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    related_entities JSONB NOT NULL DEFAULT '[]'::jsonb,
    related_decisions JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC(4,3),
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS decision_objects (
    object_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    owner TEXT,
    problem TEXT,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    alternatives JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendation TEXT,
    rationale TEXT,
    assumptions JSONB NOT NULL DEFAULT '[]'::jsonb,
    risks JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC(4,3),
    outcome TEXT,
    learning TEXT,
    related_knowledge JSONB NOT NULL DEFAULT '[]'::jsonb,
    lifecycle_state TEXT NOT NULL DEFAULT 'draft',
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enterprise_events (
    object_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    owner TEXT,
    actor TEXT,
    related_object_id UUID,
    previous_state JSONB,
    new_state JSONB,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    impact TEXT,
    lifecycle_state TEXT NOT NULL DEFAULT 'draft',
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_objects_type ON knowledge_objects (knowledge_type);
CREATE INDEX IF NOT EXISTS idx_decision_objects_type ON decision_objects (decision_type);
CREATE INDEX IF NOT EXISTS idx_enterprise_events_type ON enterprise_events (event_type);
