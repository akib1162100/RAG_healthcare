import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def query():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        q = "SELECT count(*) FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002'"
        result = await conn.execute(text(q))
        print("Count matching patient:", result.fetchone()[0])
        
        q = "SELECT metadata->>'patient_seq' FROM medical_rag_index WHERE metadata->>'patient_seq' = '20250700224002' LIMIT 1"
        result = await conn.execute(text(q))
        print("Test exact query fetch:", result.fetchall())
        
    await engine.dispose()

asyncio.run(query())
