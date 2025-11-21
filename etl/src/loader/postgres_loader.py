from src.utils.db_utils import get_connection, insert_rows
from src.config.schema_config import TABLE_NAME

def load_to_postgres(rows, db_config):
    conn = get_connection(db_config)
    try:
        insert_rows(conn, TABLE_NAME, rows)
    finally:
        conn.close()
