import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def query():
    engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/rag_healthcare'))
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT metadata->>'patient_seq' FROM medical_rag_index WHERE metadata->>'patient_seq' IS NOT NULL LIMIT 10"))
        print("patient_seq values in DB:", result.fetchall())
    await engine.dispose()

asyncio.run(query())
