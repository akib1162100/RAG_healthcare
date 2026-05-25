import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        dummy_embedding = [0.1] * 768
        embedding_str = '[' + ','.join(map(str, dummy_embedding)) + ']'
        
        # Test 1: Direct literal
        q1 = f"SELECT id FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' ORDER BY embedding <=> '{embedding_str}'::vector LIMIT 2"
        res1 = await conn.execute(text(q1))
        print("Literal query rows:", len(res1.fetchall()))

        # Test 2: Bound parameter
        q2 = "SELECT id FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' ORDER BY embedding <=> CAST(:emb AS vector) LIMIT 2"
        res2 = await conn.execute(text(q2), {'emb': embedding_str})
        print("Bound query rows:", len(res2.fetchall()))
        
    await engine.dispose()

asyncio.run(test())
