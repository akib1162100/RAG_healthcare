"""
Vector Repository - Handles pgvector database operations
Queries the unified medical_rag_index table
"""
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

TABLE_NAME = "medical_rag_index"


class VectorRepository:
    """Repository for vector database operations using pgvector"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using cosine similarity
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            metadata_filter: Optional metadata filters
            
        Returns:
            List of similar records with content, metadata, and similarity score
        """
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Build WHERE clause for metadata filtering
        where_clause = ""
        if metadata_filter:
            conditions = []
            for key, value in metadata_filter.items():
                if key == 'patient_name':
                    # Fuzzy match for names
                    conditions.append(f"metadata->>'{key}' ILIKE '%{value}%'")
                else:
                    # Exact match for IDs and other fields
                    conditions.append(f"metadata->>'{key}' = '{value}'")
            where_clause = "WHERE " + " AND ".join(conditions)
        
        search_sql = f"""
        SELECT * FROM (
            SELECT 
                id,
                content_text,
                metadata,
                odoo_model,
                odoo_res_id,
                1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM {TABLE_NAME}
            {where_clause}
        ) subquery
        ORDER BY similarity DESC
        LIMIT :limit
        """
        
        result = await self.session.execute(
            text(search_sql),
            {
                'query_embedding': embedding_str,
                'limit': limit
            }
        )
        
        rows = result.fetchall()
        
        results = []
        for row in rows:
            metadata = row[2] if row[2] else {}
            # Parse metadata if it's a string
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            results.append({
                'id': row[0],
                'content': row[1],
                'metadata': metadata,
                'source_model': row[3],
                'source_id': row[4],
                'similarity': float(row[5]) if row[5] else 0.0
            })
        
        return results
        
    async def get_patient_records(self, patient_seq: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve all raw indexed chunks directly from DB.
        Bypasses semantic similarity search.
        
        Args:
            patient_seq: Optional Odoo patient ID (seq). If None, returns all records.
            limit: Maximum number of records to return
            
        Returns:
            List of all records (content, metadata, etc.) matching the criteria
        """
        where_clause = ""
        params = {'limit': limit}
        if patient_seq:
            where_clause = "WHERE metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq
            
        query = f"""
        SELECT 
            id,
            content_text,
            metadata,
            odoo_model,
            odoo_res_id
        FROM {TABLE_NAME}
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
        
        result = await self.session.execute(
            text(query),
            params
        )
        
        rows = result.fetchall()
        
        results = []
        for row in rows:
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            results.append({
                'id': row[0],
                'content': row[1],
                'metadata': metadata,
                'source_model': row[3],
                'source_id': row[4]
            })
            
        return results
        
    async def get_prescription_records(self, patient_seq: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve all raw indexed prescription chunks directly from DB.
        Bypasses semantic similarity search.
        
        Args:
            patient_seq: Optional Odoo patient ID (seq). If None, returns all prescriptions.
            limit: Maximum number of records to return
            
        Returns:
            List of all prescription records matching the criteria
        """
        where_clause = "WHERE odoo_model = 'prescription.order.knk'"
        params = {'limit': limit}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq
            
        query = f"""
        SELECT 
            id,
            content_text,
            metadata,
            odoo_model,
            odoo_res_id
        FROM {TABLE_NAME}
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
        
        result = await self.session.execute(
            text(query),
            params
        )
        
        rows = result.fetchall()
        
        results = []
        for row in rows:
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            results.append({
                'id': row[0],
                'content': row[1],
                'metadata': metadata,
                'source_model': row[3],
                'source_id': row[4]
            })
            
        return results
    
    async def insert_embedding(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        source_model: Optional[str] = None,
        source_id: Optional[int] = None
    ) -> int:
        """Insert a single embedding"""
        metadata_json = json.dumps(metadata) if metadata else '{}'
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        insert_sql = f"""
        INSERT INTO {TABLE_NAME} (odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding)
        VALUES (:source_model, :source_id, 0, :content, CAST(:metadata AS jsonb), CAST(:embedding AS vector))
        RETURNING id
        """
        
        result = await self.session.execute(
            text(insert_sql),
            {
                'content': content,
                'embedding': embedding_str,
                'metadata': metadata_json,
                'source_model': source_model or '',
                'source_id': source_id or 0
            }
        )
        
        row = result.fetchone()
        record_id = row[0] if row else None
        
        await self.session.commit()
        
        return record_id
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        stats_sql = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT odoo_model) as unique_models,
            pg_size_pretty(pg_total_relation_size('{TABLE_NAME}')) as table_size
        FROM {TABLE_NAME}
        """
        
        result = await self.session.execute(text(stats_sql))
        row = result.fetchone()
        
        return {
            'total_records': row[0] if row else 0,
            'unique_models': row[1] if row else 0,
            'table_size': row[2] if row else '0 bytes'
        }
    
    async def delete_by_source(self, source_model: str, source_id: int) -> int:
        """Delete embeddings by source model and ID"""
        delete_sql = f"""
        DELETE FROM {TABLE_NAME}
        WHERE odoo_model = :source_model AND odoo_res_id = :source_id
        """
        
        result = await self.session.execute(
            text(delete_sql),
            {'source_model': source_model, 'source_id': source_id}
        )
        
        await self.session.commit()
        
        return result.rowcount
