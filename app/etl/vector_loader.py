"""
Vector Loader for Medical RAG Index
Loads embeddings and metadata into the medical_rag_index table
"""
from typing import List, Dict, Tuple
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
import logging

logger = logging.getLogger(__name__)


class VectorLoader:
    """Load embeddings into medical_rag_index table"""
    
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
    
    async def load_vectors(
        self,
        records: List[Tuple[str, int, int, str, Dict, List[float]]]
    ) -> int:
        """
        Bulk load vectors into medical_rag_index
        
        Args:
            records: List of tuples (odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding)
            
        Returns:
            Number of records inserted/updated
        """
        if not records:
            return 0
        
        logger.info(f"Loading {len(records)} vectors into medical_rag_index")
        
        # Use upsert to handle duplicates
        query = """
        INSERT INTO medical_rag_index 
            (odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding, created_at, updated_at)
        VALUES 
            (:odoo_model, :odoo_res_id, :chunk_index, :content_text, CAST(:metadata AS jsonb), CAST(:embedding AS vector), :created_at, :updated_at)
        ON CONFLICT (odoo_model, odoo_res_id, chunk_index)
        DO UPDATE SET
            content_text = EXCLUDED.content_text,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding,
            updated_at = EXCLUDED.updated_at
        """
        
        import json
        
        # Prepare batch data
        batch_data = []
        now = datetime.now()
        
        for odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding in records:
            # Convert embedding list to pgvector string format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            # Serialize metadata dict to JSON string
            metadata_str = json.dumps(metadata, default=str)
            
            batch_data.append({
                'odoo_model': odoo_model,
                'odoo_res_id': odoo_res_id,
                'chunk_index': chunk_index,
                'content_text': content_text,
                'metadata': metadata_str,
                'embedding': embedding_str,
                'created_at': now,
                'updated_at': now
            })
        
        # Execute batch insert
        async with self.engine.begin() as conn:
            for data in batch_data:
                await conn.execute(text(query), data)
        
        logger.info(f"Successfully loaded {len(records)} vectors")
        return len(records)
    
    async def delete_model_vectors(self, odoo_model: str, odoo_res_id: int = None):
        """
        Delete vectors for a specific model or record
        
        Args:
            odoo_model: Odoo model name
            odoo_res_id: Optional specific record ID
        """
        if odoo_res_id:
            query = """
            DELETE FROM medical_rag_index 
            WHERE odoo_model = :odoo_model AND odoo_res_id = :odoo_res_id
            """
            params = {'odoo_model': odoo_model, 'odoo_res_id': odoo_res_id}
            logger.info(f"Deleting vectors for {odoo_model} ID {odoo_res_id}")
        else:
            query = """
            DELETE FROM medical_rag_index 
            WHERE odoo_model = :odoo_model
            """
            params = {'odoo_model': odoo_model}
            logger.info(f"Deleting all vectors for {odoo_model}")
        
        async with self.engine.begin() as conn:
            result = await conn.execute(text(query), params)
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} vectors")
            return deleted_count
    
    async def get_index_stats(self) -> Dict:
        """Get statistics about the medical_rag_index"""
        query = """
        SELECT 
            odoo_model,
            COUNT(*) as total_chunks,
            COUNT(DISTINCT odoo_res_id) as unique_records,
            MIN(created_at) as first_indexed,
            MAX(updated_at) as last_updated
        FROM medical_rag_index
        GROUP BY odoo_model
        """
        
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()
            
            stats = {}
            for row in rows:
                stats[row.odoo_model] = {
                    'total_chunks': row.total_chunks,
                    'unique_records': row.unique_records,
                    'first_indexed': row.first_indexed.isoformat() if row.first_indexed else None,
                    'last_updated': row.last_updated.isoformat() if row.last_updated else None
                }
            
            return stats
