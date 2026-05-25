import asyncio
import asyncpg

async def main():
    print("Connecting to database...")
    # Adjust host to localhost for running locally outside docker
    conn = await asyncpg.connect(user='odoo', password='odoo', database='odoo', host='localhost')
    
    print("Truncating RAG tables...")
    await conn.execute("TRUNCATE TABLE medical_rag_index;")
    await conn.execute("TRUNCATE TABLE etl_metadata;")
    
    print("Unmarking Odoo sync flags...")
    models = [
        ('res_partner', 'partner_type = $1', ['patient']),
        ('wk_appointment', 'appoint_state != $1', ['rejected']),
        ('prescription_order_knk', 'state != $1', ['cancelled'])
    ]
    
    for table, condition, params in models:
        try:
            query = f"UPDATE {table} SET is_rag_synced = False WHERE {condition}"
            result = await conn.execute(query, *params)
            print(f"Updated {table}: {result}")
        except Exception as e:
            print(f"Error updating {table}: {e}")
            
    await conn.close()
    print("Flushed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
