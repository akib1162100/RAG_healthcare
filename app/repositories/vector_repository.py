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
    
    def __init__(self, session: AsyncSession, instance_id: str = "default", company_id: int = 1):
        self.session = session
        self.instance_id = instance_id
        self.company_id = company_id
    
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
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id"
        query_params = {'instance_id': self.instance_id, 'company_id': self.company_id}
        if metadata_filter:
            conditions = []
            for key, value in metadata_filter.items():
                if key == 'patient_name':
                    # Fuzzy match for names
                    conditions.append(f"metadata->>'{key}' ILIKE '%{value}%'")
                else:
                    # Exact match for IDs and other fields
                    conditions.append(f"metadata->>'{key}' = '{value}'")
            if conditions:
                where_clause += " AND " + " AND ".join(conditions)
        
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
        
        query_params.update({
            'query_embedding': embedding_str,
            'limit': limit
        })
        result = await self.session.execute(text(search_sql), query_params)
        
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
        
    async def get_patient_records(
        self,
        patient_seq: Optional[str] = None,
        limit: Optional[int] = 1000,
        offset: int = 0,
        since_id: int = 0,
        order_dir: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all raw indexed chunks directly from DB.
        Bypasses semantic similarity search.
        
        Args:
            patient_seq: Optional Odoo patient ID (seq). If None, returns all records.
            limit: Maximum number of records to return. Use None to disable the cap.
            offset: Number of matching records to skip for pagination
            since_id: Filter for records with ID strictly greater than since_id
            order_dir: "ASC" or "DESC" for ordering by created_at and id
            
        Returns:
            List of all records (content, metadata, etc.) matching the criteria
        """
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id AND id > :since_id"
        params = {'instance_id': self.instance_id, 'company_id': self.company_id, 'since_id': since_id, 'offset': offset}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq
            
        order_clause = f"ORDER BY created_at {order_dir}, id {order_dir}"
        pagination_clause = ""
        if limit is not None:
            pagination_clause += "LIMIT :limit "
            params['limit'] = limit
        if offset:
            pagination_clause += "OFFSET :offset"
            
        query = f"""
        SELECT 
            id,
            content_text,
            metadata,
            odoo_model,
            odoo_res_id
        FROM {TABLE_NAME}
        {where_clause}
        {order_clause}
        {pagination_clause}
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
                'source_id': row[4],
                'patient_seq': metadata.get('patient_seq')
            })
            
        return results
        
    async def get_prescription_records(
        self,
        patient_seq: Optional[str] = None,
        limit: Optional[int] = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all raw indexed prescription chunks directly from DB.
        Bypasses semantic similarity search.
        
        Args:
            patient_seq: Optional Odoo patient ID (seq). If None, returns all prescriptions.
            limit: Maximum number of records to return. Use None to disable the cap.
            offset: Number of matching records to skip for pagination
            
        Returns:
            List of all prescription records matching the criteria
        """
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id AND odoo_model = 'prescription.order.knk'"
        params = {'instance_id': self.instance_id, 'company_id': self.company_id, 'offset': offset}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq
        pagination_clause = ""
        if limit is not None:
            pagination_clause += "LIMIT :limit "
            params['limit'] = limit
        if offset:
            pagination_clause += "OFFSET :offset"
            
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
        {pagination_clause}
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
                'source_id': row[4],
                'patient_seq': metadata.get('patient_seq')
            })
            
        return results

    async def get_source_records(
        self,
        source_model: str,
        source_id: int,
    ) -> List[Dict[str, Any]]:
        """Fetch all chunks for a single source record, ordered by chunk index and id."""
        query = f"""
        SELECT
            id,
            content_text,
            metadata,
            odoo_model,
            odoo_res_id
        FROM {TABLE_NAME}
        WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
          AND odoo_model = :source_model AND odoo_res_id = :source_id
        ORDER BY COALESCE((metadata->>'chunk_index')::int, 0) ASC, id ASC
        """
        result = await self.session.execute(
            text(query),
            {"instance_id": self.instance_id, "company_id": self.company_id, "source_model": source_model, "source_id": source_id},
        )
        rows = result.fetchall()

        out = []
        for row in rows:
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            out.append({
                "id": row[0],
                "content": row[1],
                "metadata": metadata,
                "source_model": row[3],
                "source_id": row[4],
                "patient_seq": metadata.get("patient_seq"),
            })
        return out

    async def get_appointment_records(
        self,
        patient_seq: Optional[str] = None,
        limit: Optional[int] = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all raw indexed appointment chunks directly from DB.
        """
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id AND odoo_model = 'wk.appointment'"
        params = {'instance_id': self.instance_id, 'company_id': self.company_id, 'offset': offset}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq
        pagination_clause = ""
        if limit is not None:
            pagination_clause += "LIMIT :limit "
            params['limit'] = limit
        if offset:
            pagination_clause += "OFFSET :offset"
            
        query = f"""
        SELECT id, content_text, metadata, odoo_model, odoo_res_id
        FROM {TABLE_NAME}
        {where_clause}
        ORDER BY created_at DESC
        {pagination_clause}
        """
        result = await self.session.execute(text(query), params)
        rows = result.fetchall()
        
        results = []
        for row in rows:
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                try: metadata = json.loads(metadata)
                except: metadata = {}
            results.append({
                'id': row[0], 'content': row[1], 'metadata': metadata,
                'source_model': row[3], 'source_id': row[4],
                'patient_seq': metadata.get('patient_seq')
            })
        return results

    async def get_disease_records(self, limit: Optional[int] = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all raw indexed disease chunks directly from DB.
        """
        params = {'instance_id': self.instance_id, 'company_id': self.company_id, 'offset': offset}
        pagination_clause = ""
        if limit is not None:
            pagination_clause += "LIMIT :limit "
            params['limit'] = limit
        if offset:
            pagination_clause += "OFFSET :offset"

        query = f"""
        SELECT id, content_text, metadata, odoo_model, odoo_res_id
        FROM {TABLE_NAME}
        WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
          AND odoo_model = 'medical.disease'
        ORDER BY created_at DESC
        {pagination_clause}
        """
        result = await self.session.execute(text(query), params)
        rows = result.fetchall()
        
        results = []
        for row in rows:
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                try: metadata = json.loads(metadata)
                except: metadata = {}
            results.append({
                'id': row[0], 'content': row[1], 'metadata': metadata,
                'source_model': row[3], 'source_id': row[4]
            })
        return results

    async def count_patient_records(self, patient_seq: Optional[str] = None, since_id: int = 0) -> int:
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id AND id > :since_id"
        params = {'instance_id': self.instance_id, 'company_id': self.company_id, 'since_id': since_id}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq

        result = await self.session.execute(text(f"""
            SELECT COUNT(*)
            FROM {TABLE_NAME}
            {where_clause}
        """), params)
        return result.scalar() or 0

    async def count_prescription_records(self, patient_seq: Optional[str] = None) -> int:
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id AND odoo_model = 'prescription.order.knk'"
        params = {'instance_id': self.instance_id, 'company_id': self.company_id}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq

        result = await self.session.execute(text(f"""
            SELECT COUNT(*)
            FROM {TABLE_NAME}
            {where_clause}
        """), params)
        return result.scalar() or 0

    async def count_appointment_records(self, patient_seq: Optional[str] = None) -> int:
        where_clause = "WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id AND odoo_model = 'wk.appointment'"
        params = {'instance_id': self.instance_id, 'company_id': self.company_id}
        if patient_seq:
            where_clause += " AND metadata->>'patient_seq' = :patient_seq"
            params['patient_seq'] = patient_seq

        result = await self.session.execute(text(f"""
            SELECT COUNT(*)
            FROM {TABLE_NAME}
            {where_clause}
        """), params)
        return result.scalar() or 0

    async def count_disease_records(self) -> int:
        result = await self.session.execute(text(f"""
            SELECT COUNT(*)
            FROM {TABLE_NAME}
            WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
              AND odoo_model = 'medical.disease'
        """), {'instance_id': self.instance_id, 'company_id': self.company_id})
        return result.scalar() or 0

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
        INSERT INTO {TABLE_NAME} (odoo_instance_id, odoo_company_id, odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding)
        VALUES (:instance_id, :company_id, :source_model, :source_id, 0, :content, CAST(:metadata AS jsonb), CAST(:embedding AS vector))
        RETURNING id
        """
        
        result = await self.session.execute(
            text(insert_sql),
            {
                'content': content,
                'instance_id': self.instance_id,
                'company_id': self.company_id,
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
        WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
        """
        
        result = await self.session.execute(text(stats_sql), {'instance_id': self.instance_id, 'company_id': self.company_id})
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
        WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
          AND odoo_model = :source_model AND odoo_res_id = :source_id
        """
        
        result = await self.session.execute(
            text(delete_sql),
            {'instance_id': self.instance_id, 'company_id': self.company_id, 'source_model': source_model, 'source_id': source_id}
        )
        
        await self.session.commit()
        
        return result.rowcount

    async def get_rolling_summary(self, patient_seq: str) -> Dict[str, Any]:
        """Fetch the latest rolling summary for a patient."""
        query = """
        SELECT summary_json, last_processed_id, total_records_processed, chunk_size, is_processing
        FROM patient_rolling_summaries
        WHERE odoo_instance_id = :instance_id AND patient_seq = :patient_seq
        """
        result = await self.session.execute(text(query), {
            'instance_id': self.instance_id,
            'patient_seq': patient_seq,
        })
        row = result.fetchone()
        
        if row:
            summary = row[0]
            if isinstance(summary, str):
                try: summary = json.loads(summary)
                except: summary = {}
            return {
                'summary_json': summary,
                'last_processed_id': row[1],
                'total_records_processed': row[2] or 0,
                'chunk_size': row[3] or 0,
                'is_processing': bool(row[4]),
            }
        return {
            'summary_json': {},
            'last_processed_id': 0,
            'total_records_processed': 0,
            'chunk_size': 0,
            'is_processing': False,
        }

    async def save_rolling_summary(self, patient_seq: str, summary_json: Dict[str, Any], last_processed_id: int,
                                    chunk_size: int = 5, total_records_processed: int = 0):
        """Save/Update the rolling summary state for a patient."""
        query = """
        INSERT INTO patient_rolling_summaries
            (odoo_instance_id, patient_seq, summary_json, last_processed_id, chunk_size, total_records_processed, is_processing)
        VALUES (:instance_id, :patient_seq, CAST(:summary_json AS jsonb), :last_processed_id, :chunk_size, :total_records_processed, FALSE)
        ON CONFLICT (odoo_instance_id, patient_seq) DO UPDATE SET
            summary_json = EXCLUDED.summary_json,
            last_processed_id = EXCLUDED.last_processed_id,
            chunk_size = EXCLUDED.chunk_size,
            total_records_processed = EXCLUDED.total_records_processed,
            is_processing = FALSE,
            updated_at = CURRENT_TIMESTAMP
        """
        await self.session.execute(text(query), {
            'instance_id': self.instance_id,
            'patient_seq': patient_seq,
            'summary_json': json.dumps(summary_json),
            'last_processed_id': last_processed_id,
            'chunk_size': chunk_size,
            'total_records_processed': total_records_processed,
        })
        await self.session.commit()

    async def set_processing_flag(self, patient_seq: str, is_processing: bool) -> bool:
        """
        Set/clear the is_processing flag. Uses SKIP LOCKED to prevent concurrent generation.
        Returns True if the flag was successfully acquired (row was not already locked).
        """
        if is_processing:
            # Try to acquire the lock — skip if already locked by another worker
            result = await self.session.execute(text("""
                INSERT INTO patient_rolling_summaries (odoo_instance_id, patient_seq, is_processing)
                VALUES (:instance_id, :patient_seq, TRUE)
                ON CONFLICT (odoo_instance_id, patient_seq) DO UPDATE
                    SET is_processing = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                WHERE patient_rolling_summaries.is_processing = FALSE
                RETURNING patient_seq
            """), {'instance_id': self.instance_id, 'patient_seq': patient_seq})
            row = result.fetchone()
            await self.session.commit()
            return row is not None  # False means already locked by another worker
        else:
            await self.session.execute(text("""
                UPDATE patient_rolling_summaries
                SET is_processing = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE odoo_instance_id = :instance_id AND patient_seq = :patient_seq
            """), {'instance_id': self.instance_id, 'patient_seq': patient_seq})
            await self.session.commit()
            return True

    async def get_live_record_count(self, patient_seq: str) -> int:
        """Count total raw records in medical_rag_index for stale-detection."""
        result = await self.session.execute(text("""
            SELECT COUNT(*) FROM medical_rag_index
            WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
              AND metadata->>'patient_seq' = :patient_seq
        """), {'instance_id': self.instance_id, 'company_id': self.company_id, 'patient_seq': patient_seq})
        return result.scalar() or 0

    # ─────────────────────────────────────────────────────────────────────────
    # Chunked Summary CRUD
    # ─────────────────────────────────────────────────────────────────────────

    async def get_chunked_summaries(self, patient_seq: str, chunk_size: int) -> List[Dict[str, Any]]:
        """Fetch all cached intermediate chunk summaries for a patient at a given chunk_size, ordered oldest first."""
        result = await self.session.execute(text("""
            SELECT chunk_index, record_id_start, record_id_end, summary_json
            FROM patient_chunked_summaries
            WHERE odoo_instance_id = :instance_id
              AND patient_seq = :patient_seq AND chunk_size = :chunk_size
            ORDER BY chunk_index ASC
        """), {'instance_id': self.instance_id, 'patient_seq': patient_seq, 'chunk_size': chunk_size})
        rows = result.fetchall()
        out = []
        for row in rows:
            summary = row[3]
            if isinstance(summary, str):
                try: summary = json.loads(summary)
                except: summary = {}
            out.append({
                'chunk_index': row[0],
                'record_id_start': row[1],
                'record_id_end': row[2],
                'summary_json': summary,
            })
        return out

    async def save_chunked_summary(self, patient_seq: str, chunk_size: int, chunk_index: int,
                                    record_id_start: int, record_id_end: int, summary_json: Dict[str, Any]):
        """Upsert a single intermediate chunk summary."""
        await self.session.execute(text("""
            INSERT INTO patient_chunked_summaries
                (odoo_instance_id, patient_seq, chunk_size, chunk_index, record_id_start, record_id_end, summary_json)
            VALUES (:instance_id, :patient_seq, :chunk_size, :chunk_index, :rid_start, :rid_end, CAST(:summary_json AS jsonb))
            ON CONFLICT (odoo_instance_id, patient_seq, chunk_size, chunk_index) DO UPDATE SET
                record_id_start = EXCLUDED.record_id_start,
                record_id_end   = EXCLUDED.record_id_end,
                summary_json    = EXCLUDED.summary_json,
                updated_at      = CURRENT_TIMESTAMP
        """), {
            'instance_id': self.instance_id,
            'patient_seq': patient_seq, 'chunk_size': chunk_size, 'chunk_index': chunk_index,
            'rid_start': record_id_start, 'rid_end': record_id_end,
            'summary_json': json.dumps(summary_json),
        })
        await self.session.commit()

    async def delete_chunked_summary(self, patient_seq: str, chunk_size: int, chunk_index: int):
        """Delete a single intermediate chunk (for selective regeneration)."""
        await self.session.execute(text("""
            DELETE FROM patient_chunked_summaries
            WHERE odoo_instance_id = :instance_id
              AND patient_seq = :patient_seq AND chunk_size = :chunk_size AND chunk_index = :chunk_index
        """), {'instance_id': self.instance_id, 'patient_seq': patient_seq, 'chunk_size': chunk_size, 'chunk_index': chunk_index})
        await self.session.commit()

    async def delete_all_chunked_summaries(self, patient_seq: str):
        """Purge all intermediate chunk summaries for a patient (deep reset)."""
        await self.session.execute(text("""
            DELETE FROM patient_chunked_summaries
            WHERE odoo_instance_id = :instance_id AND patient_seq = :patient_seq
        """), {'instance_id': self.instance_id, 'patient_seq': patient_seq})
        await self.session.commit()

    async def get_alternative_chunk_summaries(self, patient_seq: str,
                                               target_chunk_size: int, source_chunk_size: int,
                                               chunk_index: int) -> List[Dict[str, Any]]:
        """
        Fetch smaller cached chunks that compose a larger target chunk.
        E.g. to build a chunk_size=15 chunk_index=0 from chunk_size=5 chunks 0,1,2.
        """
        ratio = target_chunk_size // source_chunk_size
        start_idx = chunk_index * ratio
        end_idx = start_idx + ratio - 1
        result = await self.session.execute(text("""
            SELECT chunk_index, summary_json FROM patient_chunked_summaries
            WHERE odoo_instance_id = :instance_id
              AND patient_seq = :patient_seq AND chunk_size = :chunk_size
              AND chunk_index BETWEEN :start_idx AND :end_idx
            ORDER BY chunk_index ASC
        """), {'instance_id': self.instance_id, 'patient_seq': patient_seq, 'chunk_size': source_chunk_size,
               'start_idx': start_idx, 'end_idx': end_idx})
        rows = result.fetchall()
        out = []
        for row in rows:
            summary = row[1]
            if isinstance(summary, str):
                try: summary = json.loads(summary)
                except: summary = {}
            out.append({'chunk_index': row[0], 'summary_json': summary})
        return out

    # ─────────────────────────────────────────────────────────────────────────
    # Formatted Individual Records CRUD
    # ─────────────────────────────────────────────────────────────────────────

    async def get_cached_record_ids(self, patient_seq: str) -> set:
        """Return the set of record_ids already cached for a patient (for O(1) hit/miss checks)."""
        result = await self.session.execute(text("""
            SELECT record_id FROM patient_formatted_records
            WHERE odoo_instance_id = :instance_id AND patient_seq = :patient_seq
        """), {'instance_id': self.instance_id, 'patient_seq': patient_seq})
        return {row[0] for row in result.fetchall()}

    async def get_formatted_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Fetch one cached formatted record. Returns None on cache miss."""
        result = await self.session.execute(text("""
            SELECT formatted_json FROM patient_formatted_records
            WHERE odoo_instance_id = :instance_id AND record_id = :record_id
        """), {'instance_id': self.instance_id, 'record_id': record_id})
        row = result.fetchone()
        if not row:
            return None
        data = row[0]
        if isinstance(data, str):
            try: data = json.loads(data)
            except: data = {}
        return data

    async def save_formatted_record(self, record_id: int, patient_seq: str,
                                     formatted_json: Dict[str, Any],
                                     odoo_model: str = None, odoo_res_id: int = None):
        """Insert or replace a cached formatted record."""
        await self.session.execute(text("""
            INSERT INTO patient_formatted_records
                (record_id, odoo_instance_id, patient_seq, odoo_model, odoo_res_id, formatted_json)
            VALUES (:record_id, :instance_id, :patient_seq, :odoo_model, :odoo_res_id, CAST(:formatted_json AS jsonb))
            ON CONFLICT (odoo_instance_id, record_id) DO UPDATE SET
                formatted_json = EXCLUDED.formatted_json,
                is_user_approved = FALSE,
                updated_at = CURRENT_TIMESTAMP
        """), {
            'record_id': record_id, 'instance_id': self.instance_id, 'patient_seq': patient_seq,
            'odoo_model': odoo_model, 'odoo_res_id': odoo_res_id,
            'formatted_json': json.dumps(formatted_json),
        })
        await self.session.commit()

    async def delete_formatted_record(self, record_id: int):
        """Remove one cached formatted record (triggers re-generation on next request)."""
        await self.session.execute(text("""
            DELETE FROM patient_formatted_records
            WHERE odoo_instance_id = :instance_id AND record_id = :record_id
        """), {'instance_id': self.instance_id, 'record_id': record_id})
        await self.session.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # Audit log
    # ─────────────────────────────────────────────────────────────────────────

    async def log_regeneration(self, patient_seq: str, regeneration_type: str,
                                triggered_by: str = 'api',
                                chunk_index: int = None, record_id: int = None):
        """Write a row to the audit log table."""
        await self.session.execute(text("""
            INSERT INTO summary_regeneration_log
                (patient_seq, regeneration_type, chunk_index, record_id, triggered_by)
            VALUES (:patient_seq, :regen_type, :chunk_index, :record_id, :triggered_by)
        """), {
            'patient_seq': patient_seq, 'regen_type': regeneration_type,
            'chunk_index': chunk_index, 'record_id': record_id, 'triggered_by': triggered_by,
        })
        await self.session.commit()

    async def get_all_stale_patients(self) -> List[str]:
        """Return patient_seqs where total_records_processed < live count (for nightly scheduler)."""
        result = await self.session.execute(text("""
            SELECT prs.patient_seq
            FROM patient_rolling_summaries prs
            JOIN (
                SELECT metadata->>'patient_seq' AS patient_seq, COUNT(*) AS live_count
                FROM medical_rag_index
                WHERE odoo_instance_id = :instance_id AND odoo_company_id = :company_id
                  AND metadata->>'patient_seq' IS NOT NULL
                GROUP BY metadata->>'patient_seq'
            ) live ON live.patient_seq = prs.patient_seq
            WHERE prs.odoo_instance_id = :instance_id
              AND prs.is_processing = FALSE
              AND prs.total_records_processed < live.live_count
        """), {'instance_id': self.instance_id, 'company_id': self.company_id})
        return [row[0] for row in result.fetchall()]

