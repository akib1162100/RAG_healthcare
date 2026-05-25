import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def check():
    engine = create_async_engine("postgresql+asyncpg://odoo:odoo@localhost:5432/odoo_db")
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, state, is_rag_synced, write_date FROM prescription_order_knk WHERE name='PRE0066'"))
        row = res.fetchone()
        print("PRE0066:", row)
        res2 = await conn.execute(text("SELECT count(*) FROM prescription_order_knk WHERE state != 'cancelled'"))
        row2 = res2.fetchone()
        print("Total non-cancelled:", row2)
        res3 = await conn.execute(text("SELECT count(*) FROM prescription_order_knk WHERE state != 'cancelled' AND is_rag_synced IS NOT TRUE"))
        row3 = res3.fetchone()
        print("Total non-cancelled and not synced:", row3)
    await engine.dispose()

asyncio.run(check())
