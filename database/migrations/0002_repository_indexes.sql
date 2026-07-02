-- SmartCoat Release 1.5 repository support indexes

CREATE INDEX IF NOT EXISTS idx_knowledge_objects_domain ON knowledge_objects (domain);
CREATE INDEX IF NOT EXISTS idx_knowledge_objects_lifecycle_state ON knowledge_objects (lifecycle_state);

CREATE INDEX IF NOT EXISTS idx_decision_objects_status ON decision_objects (status);
CREATE INDEX IF NOT EXISTS idx_decision_objects_domain ON decision_objects (domain);

CREATE INDEX IF NOT EXISTS idx_enterprise_events_related_object_id ON enterprise_events (related_object_id);
CREATE INDEX IF NOT EXISTS idx_enterprise_events_created_at ON enterprise_events (created_at);
