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
                odoo_model VARCHAR(255) NOT NULL,
                odoo_res_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0,
                content_text TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(odoo_model, odoo_res_id, chunk_index)
            )
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
                odoo_model VARCHAR(255) UNIQUE NOT NULL,
                last_indexed_at TIMESTAMP,
                last_write_date TIMESTAMP,
                total_records INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 0
            )
        """))
        logger.info("etl_metadata table ready")
    
    logger.info("Database initialization complete")
