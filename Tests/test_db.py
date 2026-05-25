import asyncio
import asyncpg

TABLES = ['dose_dose','frequency_frequency','route_route','when_to_take']

async def check():
    conn = await asyncpg.connect('postgresql://odoo16:odoo16@host.docker.internal:5432/clidram_16')
    for t in TABLES:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=$1)", t
        )
        if exists:
            cols = await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name=$1 ORDER BY ordinal_position", t
            )
            print(f"{t}: {', '.join([c[0] for c in cols])}")
        else:
            print(f"{t}: DOES NOT EXIST")
    await conn.close()

asyncio.run(check())
