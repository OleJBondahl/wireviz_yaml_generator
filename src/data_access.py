"""
Data Access Layer.

This module implements the Repository Pattern for SQLite access.
It handles all raw SQL interactions and maps database rows to 
strongly-typed Domain Models (`models.py`).

Usage:
    source = SqliteDataSource(db_filepath)
    nets = source.load_net_table("W001")
"""

import sqlite3
from typing import List, Dict, Any
from models import NetRow, DesignatorRow, ConnectorRow, CableRow
from exceptions import DatabaseError

class SqliteDataSource:
    """
    A unified data source adapter for the SQLite database.
    """

    def __init__(self, db_filepath: str):
        self.db_filepath = db_filepath

    def _fetch_dict_rows(self, query: str) -> List[Dict[str, Any]]:
        """
        Internal: Executes a raw SQL query and returns results as dictionaries.
        
        Raises:
            DatabaseError: If database connection fails or query errors.
        """
        try:
            conn = sqlite3.connect(self.db_filepath, detect_types=0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError as e:
            raise DatabaseError(f"Database operation failed in '{self.db_filepath}': {e}") from e

    def _build_query(self, table_name: str, where_clause: str = "") -> str:
        """Helper to construct simple SELECT * queries."""
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        return query

    def check_cable_existence(self, cable_des: str) -> bool:
        """
        Checks if a specific cable exists in the NetTable.
        """
        query = f"SELECT 1 FROM NetTable WHERE cable_des = '{cable_des}' LIMIT 1"
        try:
            conn = sqlite3.connect(self.db_filepath)
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()
            return bool(result)
        except sqlite3.OperationalError:
            return False

    # --- Domain Loaders ---

    def load_net_table(self, cable_des_filter: str = "") -> List[NetRow]:
        where = f"cable_des = '{cable_des_filter}'" if cable_des_filter else ""
        rows = self._fetch_dict_rows(self._build_query("NetTable", where))
        
        return [
            NetRow(
                cable_des=row.get('cable_des'),
                comp_des_1=row.get('comp_des_1'),
                conn_des_1=row.get('conn_des_1'),
                pin_1=row.get('pin_1'),
                comp_des_2=row.get('comp_des_2'),
                conn_des_2=row.get('conn_des_2'),
                pin_2=row.get('pin_2'),
                net_name=row.get('net_name')
            ) for row in rows
        ]

    def load_designator_table(self) -> List[DesignatorRow]:
        rows = self._fetch_dict_rows(self._build_query("DesignatorTable"))
        return [
            DesignatorRow(
                comp_des=row.get('comp_des'),
                conn_des=row.get('conn_des'),
                conn_mpn=row.get('conn_mpn')
            ) for row in rows
        ]

    def load_connector_table(self) -> List[ConnectorRow]:
        rows = self._fetch_dict_rows(self._build_query("ConnectorTable"))
        return [
            ConnectorRow(
                mpn=row.get('mpn'),
                pincount=row.get('pincount'),
                mate_mpn=row.get('mate_mpn'),
                pin_mpn=row.get('pin_mpn'),
                description=row.get('description', ''),
                manufacturer=row.get('manufacturer', '')
            ) for row in rows
        ]

    def load_cable_table(self) -> List[CableRow]:
        rows = self._fetch_dict_rows(self._build_query("CableTable"))
        return [
            CableRow(
                cable_des=row.get('cable_des'),
                wire_gauge=row.get('wire_gauge'),
                length=row.get('length'),
                note=row.get('note')
            ) for row in rows
        ]
