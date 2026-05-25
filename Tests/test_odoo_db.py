import psycopg2

def main():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="odoo16",
            password="odoo16",
            host="localhost",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cur.fetchall()
        print("Available databases:")
        for r in rows:
            print(f"  {r[0]}")
    except Exception as e:
        print("Error connecting to postgres:", e)

if __name__ == "__main__":
    main()
