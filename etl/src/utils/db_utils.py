import psycopg2
from psycopg2.extras import execute_values

def get_connection(db_config):
    return psycopg2.connect(**db_config)

def insert_rows(conn, table, rows):
    if not rows:
        return
    columns = rows[0].keys()
    values = [[row[col] for col in columns] for row in rows]
    with conn.cursor() as cur:
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
        execute_values(cur, query, values)
    conn.commit()
