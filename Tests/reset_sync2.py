import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('ODOO_DATABASE_URL')
print('Connecting to:', db_url)

async def reset():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE prescription_order_knk SET is_rag_synced = FALSE"))
        print('Reset sync status for all prescriptions.')

asyncio.run(reset())
