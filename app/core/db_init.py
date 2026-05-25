"""
Database initialization script
Creates required tables and extensions for the RAG Healthcare System
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def init_database(engine: AsyncEngine):
    """
    Initialize database with required extensions and tables.
    Should be called on application startup.
    """
    logger.info("Initializing database schema...")
    
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension ready")
        
        # Create medical_rag_index table (unified vector storage)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS medical_rag_index (
                id SERIAL PRIMARY KEY,
                odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
                odoo_company_id INTEGER NOT NULL DEFAULT 1,
                odoo_model VARCHAR(255) NOT NULL,
                odoo_res_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0,
                content_text TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(odoo_instance_id, odoo_company_id, odoo_model, odoo_res_id, chunk_index)
            )
        """))
        await conn.execute(text("""
            ALTER TABLE medical_rag_index
            ADD COLUMN IF NOT EXISTS odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
            ADD COLUMN IF NOT EXISTS odoo_company_id INTEGER NOT NULL DEFAULT 1
        """))
        await conn.execute(text("""
            ALTER TABLE medical_rag_index
            DROP CONSTRAINT IF EXISTS medical_rag_index_odoo_model_odoo_res_id_chunk_index_key,
            DROP CONSTRAINT IF EXISTS medical_rag_index_odoo_instance_id_odoo_model_odoo_res__key,
            DROP CONSTRAINT IF EXISTS uq_rag_index_instance_company_model_res_chunk
        """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS medical_rag_index_instance_company_unique
            ON medical_rag_index (odoo_instance_id, odoo_company_id, odoo_model, odoo_res_id, chunk_index)
        """))
        logger.info("medical_rag_index table ready")
        
        # Create IVFFlat index for fast similarity search
        # Only create if enough rows exist (IVFFlat needs data)
        row_count = await conn.execute(text(
            "SELECT COUNT(*) FROM medical_rag_index"
        ))
        count = row_count.scalar()
        
        if count and count >= 100:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS medical_rag_index_embedding_idx
                ON medical_rag_index USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            logger.info("IVFFlat index created")
        else:
            # Use HNSW index which works with any number of rows
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS medical_rag_index_embedding_hnsw_idx
                ON medical_rag_index USING hnsw (embedding vector_cosine_ops)
            """))
            logger.info("HNSW index ready")
        
        # Create ETL metadata table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS etl_metadata (
                id SERIAL PRIMARY KEY,
                odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
                odoo_company_id INTEGER NOT NULL DEFAULT 1,
                odoo_model VARCHAR(255) NOT NULL,
                last_indexed_at TIMESTAMP,
                last_write_date TIMESTAMP,
                total_records INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 0,
                UNIQUE (odoo_instance_id, odoo_company_id, odoo_model)
            )
        """))
        await conn.execute(text("""
            ALTER TABLE etl_metadata
            ADD COLUMN IF NOT EXISTS odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
            ADD COLUMN IF NOT EXISTS odoo_company_id INTEGER NOT NULL DEFAULT 1
        """))
        await conn.execute(text("""
            ALTER TABLE etl_metadata
            DROP CONSTRAINT IF EXISTS etl_metadata_odoo_model_key,
            DROP CONSTRAINT IF EXISTS etl_metadata_odoo_instance_id_odoo_model_key
        """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS etl_metadata_instance_company_unique
            ON etl_metadata (odoo_instance_id, odoo_company_id, odoo_model)
        """))
        logger.info("etl_metadata table ready")
        
        # Create rolling summaries table (extended)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patient_rolling_summaries (
                odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
                patient_seq VARCHAR(255) PRIMARY KEY,
                summary_json JSONB DEFAULT '{}',
                last_processed_id INTEGER DEFAULT 0,
                chunk_size INTEGER DEFAULT 5,
                total_records_processed INTEGER DEFAULT 0,
                is_processing BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("""
            ALTER TABLE patient_rolling_summaries
            ADD COLUMN IF NOT EXISTS odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default'
        """))
        await conn.execute(text("""
            ALTER TABLE patient_rolling_summaries
            DROP CONSTRAINT IF EXISTS patient_rolling_summaries_pkey
        """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS patient_rolling_summaries_instance_unique
            ON patient_rolling_summaries (odoo_instance_id, patient_seq)
        """))
        # Add new columns to existing rows gracefully (ALTER IF NOT EXISTS)
        for col_def in [
            "chunk_size INTEGER DEFAULT 5",
            "total_records_processed INTEGER DEFAULT 0",
            "is_processing BOOLEAN DEFAULT FALSE",
            "odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        ]:
            col_name = col_def.split()[0]
            await conn.execute(text(f"""
                DO $$ BEGIN
                    ALTER TABLE patient_rolling_summaries ADD COLUMN IF NOT EXISTS {col_def};
                EXCEPTION WHEN duplicate_column THEN NULL;
                END $$;
            """))
        logger.info("patient_rolling_summaries table ready")

        # ── NEW: Hierarchical chunk summaries ──────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patient_chunked_summaries (
                id SERIAL PRIMARY KEY,
                odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
                patient_seq VARCHAR(255) NOT NULL,
                chunk_size INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                record_id_start INTEGER NOT NULL,
                record_id_end INTEGER NOT NULL,
                summary_json JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (odoo_instance_id, patient_seq, chunk_size, chunk_index)
            )
        """))
        await conn.execute(text("""
            ALTER TABLE patient_chunked_summaries
            ADD COLUMN IF NOT EXISTS odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default'
        """))
        await conn.execute(text("""
            ALTER TABLE patient_chunked_summaries
            DROP CONSTRAINT IF EXISTS patient_chunked_summaries_patient_seq_chunk_size_chunk_index_key
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunked_summaries_patient
            ON patient_chunked_summaries (odoo_instance_id, patient_seq, chunk_size)
        """))
        logger.info("patient_chunked_summaries table ready")

        # ── NEW: Formatted individual records cache ───────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patient_formatted_records (
                id SERIAL PRIMARY KEY,
                record_id INTEGER NOT NULL,
                odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default',
                patient_seq VARCHAR(255) NOT NULL,
                odoo_model VARCHAR(255),
                odoo_res_id INTEGER,
                formatted_json JSONB DEFAULT '{}',
                is_user_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (odoo_instance_id, record_id)
            )
        """))
        await conn.execute(text("""
            ALTER TABLE patient_formatted_records
            ADD COLUMN IF NOT EXISTS odoo_instance_id VARCHAR(100) NOT NULL DEFAULT 'default'
        """))
        await conn.execute(text("""
            ALTER TABLE patient_formatted_records
            DROP CONSTRAINT IF EXISTS patient_formatted_records_record_id_key
        """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS patient_formatted_records_instance_record_unique
            ON patient_formatted_records (odoo_instance_id, record_id)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_formatted_records_patient
            ON patient_formatted_records (odoo_instance_id, patient_seq)
        """))
        logger.info("patient_formatted_records table ready")

        # ── NEW: Regeneration audit log ───────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS summary_regeneration_log (
                id SERIAL PRIMARY KEY,
                patient_seq VARCHAR(255) NOT NULL,
                regeneration_type VARCHAR(50) NOT NULL,  -- 'soft', 'deep', 'chunk', 'record'
                chunk_index INTEGER,                     -- NULL unless type=chunk
                record_id INTEGER,                       -- NULL unless type=record
                triggered_by VARCHAR(255),               -- Odoo uid or 'scheduler'
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        logger.info("summary_regeneration_log table ready")
    
    logger.info("Database initialization complete")
