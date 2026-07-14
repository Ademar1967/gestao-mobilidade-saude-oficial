import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

tables = [
    row[0]
    for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
]
for table in tables:
    if table.startswith("sqlite_"):
        continue
    print(f"\n--- {table} ---")
    try:
        cols = [
            desc[0]
            for desc in cursor.execute(f"SELECT * FROM {table} LIMIT 1").description
        ]
        for col in cols:
            try:
                cursor.execute(
                    f"SELECT rowid, {col} FROM {table} WHERE typeof({col})='text' AND {col} LIKE '%/%/%/%/%' LIMIT 5"
                )
                for row in cursor.fetchall():
                    print(f"rowid={row[0]} {col}={row[1]}")
            except Exception as e:
                pass
    except Exception as e:
        print(f"Erro: {e}")
conn.close()
print("\nBusca concluída.")
