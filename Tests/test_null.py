import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        q = "SELECT id, embedding IS NULL FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' LIMIT 5"
        result = await conn.execute(text(q))
        print("Embeddings are NULL?", result.fetchall())
        
    await engine.dispose()

asyncio.run(test())
