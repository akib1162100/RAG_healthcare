import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def reset():
    engine = create_async_engine('postgresql+asyncpg://odoo:odoo@localhost/Clidram_Live')
    async with engine.begin() as conn:
        await conn.execute(text('UPDATE prescription_order_knk SET is_rag_synced = FALSE'))
        print('Reset sync status for all prescriptions.')

asyncio.run(reset())
