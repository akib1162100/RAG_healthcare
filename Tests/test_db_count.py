import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def count():
    engine = create_async_engine(os.getenv('ODOO_DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/postgres'))
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT state, COUNT(*) FROM prescription_order_knk GROUP BY state'))
        print(result.fetchall())
    await engine.dispose()

asyncio.run(count())
