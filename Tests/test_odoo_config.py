import psycopg2

def main():
    try:
        conn = psycopg2.connect(
            dbname="clidram_16",
            user="odoo16",
            password="odoo16",
            host="localhost",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM ir_config_parameter WHERE key LIKE 'rag_controller.%';")
        rows = cur.fetchall()
        print("ir_config_parameter RAG Settings:")
        for r in rows:
            print(f"  {r[0]}: {r[1]}")
    except Exception as e:
        print("Error connecting to postgres:", e)

if __name__ == "__main__":
    main()
