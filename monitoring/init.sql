CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    question TEXT NOT NULL,
    answer TEXT,
    model TEXT DEFAULT 'gpt-4o-mini',
    response_time_ms INTEGER,
    tool_calls_count SMALLINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS retrieved_docs (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES queries(id) ON DELETE CASCADE,
    rank SMALLINT,
    doc_id TEXT,
    score FLOAT,
    chapter TEXT,
    section TEXT,
    doc_type TEXT -- 'prose' | 'commands'
);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES queries(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ DEFAULT NOW(),
    rating SMALLINT -- 1 = 👍, -1 = 👎
);

-- Indexes used by Grafana queries
CREATE INDEX IF NOT EXISTS idx_queries_ts ON queries(ts);
CREATE INDEX IF NOT EXISTS idx_feedback_query ON feedback(query_id);
CREATE INDEX IF NOT EXISTS idx_retrieved_query ON retrieved_docs(query_id);
