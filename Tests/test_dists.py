import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        q = "SELECT embedding::text FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' LIMIT 1"
        res = await conn.execute(text(q))
        real_vector_str = res.fetchone()[0]
        
        q2 = "SELECT id, embedding <=> CAST(:emb AS vector) as dist FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002'"
        res2 = await conn.execute(text(q2), {'emb': real_vector_str})
        rows = res2.fetchall()
        print("Distances computed:")
        for r in rows:
            print(f"ID: {r[0]}, dist: {r[1]}")
            
    await engine.dispose()

asyncio.run(test())
