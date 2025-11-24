from src.utils.db_utils import get_connection, insert_rows


def load_to_postgres(rows, db_config, table):
    conn = get_connection(db_config)
    try:
        insert_rows(conn, table, rows)
    finally:
        conn.close()
