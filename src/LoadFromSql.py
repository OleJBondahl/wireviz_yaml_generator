import sqlite3
from typing import List, Dict, Any
import sys

def fetch_data(query: str, db_filepath: str) -> List[Dict[str, Any]]:
  #fetch data from sql database master.db, with a sql query str
    try:
        # connect with detect_types=0 to ensure all data is read as strings
        conn = sqlite3.connect(db_filepath, detect_types=0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError as e:
        print(f"❌ Database Error: {e} in database '{db_filepath}'")
        print("   Please ensure the database file is correct and contains the required tables.")
        sys.exit(1) # Exit the script because it cannot continue.


def build_query(TABLE_NAME: str, query_type: str = "SELECT * ", where_clause: str = "") -> str:
    query = query_type + " FROM " + TABLE_NAME
    if where_clause:
        query += " WHERE " + where_clause
    return query

def fetch_table(table_name: str, db_filepath: str, where_clause: str = "") -> List[Dict[str, Any]]:
    query = build_query(table_name, where_clause=where_clause)
    data = fetch_data(query, db_filepath)
    return data
  
