import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.repositories.vector_repository import VectorRepository

async def test_search():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        repo = VectorRepository(conn)
        dummy_embedding = [0.1] * 768
        
        # Build where clause manually to see what search_similar does
        metadata_filter = {'patient_seq': '20250700224002'}
        conditions = []
        for key, value in metadata_filter.items():
            conditions.append(f"metadata->>'{key}' = '{value}'")
        where_clause = "WHERE " + " AND ".join(conditions)
        
        search_sql = f"""
        SELECT id, content_text
        FROM medical_rag_index
        {where_clause}
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT 5
        """
        
        print("Executing SQL:\n", search_sql)
        embedding_str = '[' + ','.join(map(str, dummy_embedding)) + ']'
        
        try:
            result = await conn.execute(text(search_sql), {'query_embedding': embedding_str})
            rows = result.fetchall()
            print(f"Direct text query returned {len(rows)} rows")
            
            # Now call the actual method
            results = await repo.search_similar(dummy_embedding, limit=5, metadata_filter=metadata_filter)
            print(f"Repo search_similar returned {len(results)} rows")
        except Exception as e:
            print(f"Error: {e}")
            
    await engine.dispose()

asyncio.run(test_search())
