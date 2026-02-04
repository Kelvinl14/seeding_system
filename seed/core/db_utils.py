import logging
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

def fast_insert(cur, table, columns, values, on_conflict=None):
    """
    Optimized batch insert using execute_values.
    """
    cols_str = ",".join(columns)
    query = f"INSERT INTO {table} ({cols_str}) VALUES %s"
    if on_conflict:
        query += f" ON CONFLICT {on_conflict}"
    
    execute_values(cur, query, values)

def get_existing_ids(cur, table, column="id"):
    """
    Fetch all existing IDs from a table.
    """
    cur.execute(f"SELECT {column} FROM {table}")
    return [row[column] for row in cur.fetchall()]

def toggle_constraints(cur, table, enable=True):
    """
    Disable/Enable triggers for performance. Use with caution.
    """
    action = "ENABLE" if enable else "DISABLE"
    cur.execute(f"ALTER TABLE {table} {action} TRIGGER ALL")
