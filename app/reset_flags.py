import asyncio
import sys
import logging

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    else:
        db_url = "postgresql+asyncpg://odoo16:odoo16@host.docker.internal:5432/clidram_16"

    engine = create_async_engine(db_url, echo=False)
    
    query = """
    UPDATE prescription_order_knk 
    SET is_rag_synced = False 
    WHERE state != 'cancelled'
    """
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(query))
            logger.info(f"Reset {result.rowcount} prescriptions to be re-synced.")
    except Exception as e:
        logger.error(f"Failed to reset sync flags: {e}")
    finally:
        await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
