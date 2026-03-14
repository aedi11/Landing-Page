-- ============================================================================
-- AEDI Battery Pack Pipeline — Supabase Schema: design_rules table (pgvector)
-- UPDATED to support electrical, thermal, and mechanical JSON rule files
-- Execute this in Supabase SQL Editor AFTER 01_cells_table.sql
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS design_rules CASCADE;

CREATE TABLE design_rules (
    id              SERIAL PRIMARY KEY,

    -- Rule classification (matches JSON rule_type field)
    rule_type       TEXT NOT NULL,               -- Electrical, Thermal, Mechanical, Safety, Performance, Regulatory
    category        TEXT,                         -- voltage, current, thermal, safety, etc. (derived)

    -- Rule content
    constraint_expr TEXT NOT NULL,                -- The actual rule text
    severity        TEXT NOT NULL DEFAULT 'Warning'
                    CHECK (severity IN ('Critical', 'Warning', 'Recommendation')),
    source          TEXT,                         -- e.g. 'The-Handbook-of-Lithium-Ion-Battery-Pack-Design.txt'
    applies_to      TEXT,                         -- Cell, Pack, Module, BMS, All, Thermal, Wiring, Charging

    -- Structured parameters
    parameter       TEXT,                         -- e.g. 'voltage', 'temperature', 'DOD'
    min_value       FLOAT,
    max_value       FLOAT,
    nominal_value   FLOAT,
    unit            TEXT,

    -- Full JSON blob for any extra fields
    raw_json        JSONB DEFAULT '{}',

    -- pgvector embedding for semantic RAG search
    embedding       vector(1536),                 -- OpenAI text-embedding-3-small

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rules_rule_type ON design_rules(rule_type);
CREATE INDEX idx_rules_severity ON design_rules(severity);
CREATE INDEX idx_rules_applies_to ON design_rules(applies_to);
CREATE INDEX idx_rules_parameter ON design_rules(parameter);
CREATE INDEX idx_rules_category ON design_rules(category);

-- Vector similarity search index
-- NOTE: IVFFlat requires at least (lists * 10) rows to build.
-- If you have <200 rules, use HNSW instead or skip this and create after data load.
-- For small datasets, cosine similarity works fine without an index.
CREATE INDEX idx_rules_embedding
    ON design_rules USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- Helper function: semantic search for design rules
-- ============================================================================
CREATE OR REPLACE FUNCTION match_design_rules(
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    match_threshold FLOAT DEFAULT 0.5,
    filter_rule_type TEXT DEFAULT NULL,
    filter_severity TEXT DEFAULT NULL,
    filter_applies_to TEXT DEFAULT NULL,
    filter_parameter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    rule_type TEXT,
    category TEXT,
    constraint_expr TEXT,
    severity TEXT,
    source TEXT,
    applies_to TEXT,
    parameter TEXT,
    min_value FLOAT,
    max_value FLOAT,
    nominal_value FLOAT,
    unit TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dr.id,
        dr.rule_type,
        dr.category,
        dr.constraint_expr,
        dr.severity,
        dr.source,
        dr.applies_to,
        dr.parameter,
        dr.min_value,
        dr.max_value,
        dr.nominal_value,
        dr.unit,
        1 - (dr.embedding <=> query_embedding) AS similarity
    FROM design_rules dr
    WHERE
        dr.embedding IS NOT NULL
        AND (filter_rule_type IS NULL OR dr.rule_type = filter_rule_type)
        AND (filter_severity IS NULL OR dr.severity = filter_severity)
        AND (filter_applies_to IS NULL OR dr.applies_to = filter_applies_to)
        AND (filter_parameter IS NULL OR dr.parameter = filter_parameter)
        AND 1 - (dr.embedding <=> query_embedding) > match_threshold
    ORDER BY dr.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- Helper function: fetch rules by exact filters (no embedding needed)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_rules_by_filter(
    filter_rule_type TEXT DEFAULT NULL,
    filter_severity TEXT DEFAULT NULL,
    filter_applies_to TEXT DEFAULT NULL,
    filter_parameter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    rule_type TEXT,
    constraint_expr TEXT,
    severity TEXT,
    applies_to TEXT,
    parameter TEXT,
    min_value FLOAT,
    max_value FLOAT,
    nominal_value FLOAT,
    unit TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dr.id,
        dr.rule_type,
        dr.constraint_expr,
        dr.severity,
        dr.applies_to,
        dr.parameter,
        dr.min_value,
        dr.max_value,
        dr.nominal_value,
        dr.unit
    FROM design_rules dr
    WHERE
        (filter_rule_type IS NULL OR dr.rule_type = filter_rule_type)
        AND (filter_severity IS NULL OR dr.severity = filter_severity)
        AND (filter_applies_to IS NULL OR dr.applies_to = filter_applies_to)
        AND (filter_parameter IS NULL OR dr.parameter = filter_parameter)
    ORDER BY
        CASE dr.severity
            WHEN 'Critical' THEN 1
            WHEN 'Warning' THEN 2
            WHEN 'Recommendation' THEN 3
        END;
END;
$$;
