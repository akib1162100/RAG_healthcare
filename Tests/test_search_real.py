import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        # Get a real vector
        q = "SELECT embedding::text FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' LIMIT 1"
        res = await conn.execute(text(q))
        row = res.fetchone()
        if not row:
            print("No vector found")
            return
            
        real_vector_str = row[0]
        
        # Now query with it
        q2 = "SELECT id FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' ORDER BY embedding <=> CAST(:emb AS vector) LIMIT 5"
        res2 = await conn.execute(text(q2), {'emb': real_vector_str})
        rows = res2.fetchall()
        print("Rows returned with real vector:", len(rows))
        print("IDs:", rows)
        
    await engine.dispose()

asyncio.run(test())
