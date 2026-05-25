-- Initialize pgvector extension for medical RAG system
-- This script creates the vector extension and medical_rag_index table

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create medical RAG index table
CREATE TABLE IF NOT EXISTS medical_rag_index (
    id SERIAL PRIMARY KEY,
    odoo_model VARCHAR(100) NOT NULL,  -- e.g., 'wk.appointment', 'prescription.order.knk'
    odoo_res_id INTEGER NOT NULL,      -- Odoo record ID
    chunk_index INTEGER DEFAULT 0,      -- For multi-chunk records
    content_text TEXT NOT NULL,         -- Flattened human-readable content
    metadata JSONB NOT NULL DEFAULT '{}',  -- Additional context for filtering
    embedding VECTOR(768),              -- ClinicalBERT embedding (768 dimensions)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(odoo_model, odoo_res_id, chunk_index)  -- Prevent duplicates
);

-- Create indexes for performance
-- GIN index for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_medical_rag_metadata 
    ON medical_rag_index USING GIN (metadata);

-- B-tree index for model and resource ID lookups
CREATE INDEX IF NOT EXISTS idx_medical_rag_model_res 
    ON medical_rag_index (odoo_model, odoo_res_id);

-- HNSW index for fast approximate nearest neighbor search
-- For ClinicalBERT (768 dims), m=16 and ef_construction=64 are good defaults
CREATE INDEX IF NOT EXISTS idx_medical_rag_embedding 
    ON medical_rag_index USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 64);

-- Create metadata tracking table for ETL pipeline
CREATE TABLE IF NOT EXISTS etl_metadata (
    id SERIAL PRIMARY KEY,
    odoo_model VARCHAR(100) UNIQUE NOT NULL,
    last_indexed_at TIMESTAMP,
    last_write_date TIMESTAMP,  -- Track last Odoo write_date processed
    total_records INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0
);

-- Insert initial tracking records for core models
INSERT INTO etl_metadata (odoo_model, total_records, total_chunks)
VALUES 
    ('wk.appointment', 0, 0),
    ('prescription.order.knk', 0, 0),
    ('res.partner', 0, 0)
ON CONFLICT (odoo_model) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_medical_rag_index_updated_at 
    BEFORE UPDATE ON medical_rag_index
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON medical_rag_index TO odoo;
-- GRANT SELECT, INSERT, UPDATE ON etl_metadata TO odoo;
