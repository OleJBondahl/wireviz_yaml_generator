import sqlite3
from typing import List, Dict, Any
import sys

def fetch_data(query: str, db_filepath: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query and fetches all results from the specified database.

    Connects to the SQLite database, executes the given query, and returns the
    results as a list of dictionaries. It includes error handling for database
    connection issues.

    Args:
        query: The SQL query string to execute.
        db_filepath: The file path to the SQLite database.

    Returns:
        A list of dictionaries, where each dictionary represents a row from the result set.
    """
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
    """
    Constructs a SQL query string from component parts.

    Args:
        TABLE_NAME: The name of the table to query.
        query_type: The type of query (e.g., "SELECT *").
        where_clause: An optional WHERE clause to filter results (without the 'WHERE' keyword).

    Returns:
        A fully formed SQL query string.
    """
    query = query_type + " FROM " + TABLE_NAME
    if where_clause:
        query += " WHERE " + where_clause
    return query

def fetch_table(table_name: str, db_filepath: str, where_clause: str = "") -> List[Dict[str, Any]]:
    """
    Fetches all data from a specified table, with an optional filter.

    Args:
        table_name: The name of the database table to fetch from.
        db_filepath: The file path to the SQLite database.
        where_clause: An optional SQL WHERE clause to filter the results.

    Returns:
        A list of dictionaries, where each dictionary is a row from the table.
    """
    query = build_query(table_name, where_clause=where_clause)
    data = fetch_data(query, db_filepath)
    return data
  
