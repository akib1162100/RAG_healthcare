import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        q = "SELECT id, embedding_sum FROM (SELECT id, SELECT sum(x) FROM unnest(string_to_array(btrim(embedding::text, '[]'), ',')::float[]) as x as embedding_sum FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' LIMIT 5) t"
        
        # simpler way to check if it's all zeros using l2 norm
        q = "SELECT id, (embedding <-> CAST('[0,0,0...]' AS vector)) IS NULL FROM medical_rag_index LIMIT 1"
        # actually let's just get the vector and sum it in python
        q = "SELECT id, embedding::text FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' LIMIT 2"
        result = await conn.execute(text(q))
        
        rows = result.fetchall()
        for r in rows:
            vec = [float(x) for x in r[1][1:-1].split(',')]
            print(f"ID {r[0]} sum: {sum(vec)}, norm: {sum(x*x for x in vec)}")
        
    await engine.dispose()

asyncio.run(test())
