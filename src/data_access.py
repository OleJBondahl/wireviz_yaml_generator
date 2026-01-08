"""
Data Access Layer - Repository Pattern Implementation.

This module implements the Repository Pattern to isolate database access from
business logic. It handles all SQL interactions and maps database rows to
strongly-typed domain models defined in models.py.

Design Philosophy:
    - Single Responsibility: Only handles data retrieval
    - Type Safety: Returns domain objects, not raw SQL results
    - Error Handling: Converts database errors to application exceptions
    - No Business Logic: Pure data access, no transformations

Database Schema:
    Expected tables (see DATABASE_SCHEMA.md for details):
    - NetTable: Point-to-point connections (cable_des, comp_des, pin, net_name)
    - DesignatorTable: Component-to-connector mapping (comp_des, conn_des, conn_mpn)
    - ConnectorTable: Connector catalog (mpn, pincount, description, manufacturer)
    - CableTable: Cable physical properties (cable_des, wire_gauge, length, note)

Example:
    >>> source = SqliteDataSource("data/master.db")
    >>> nets = source.load_net_table("W001")  # Get all connections for cable W001
    >>> connectors = source.load_connector_table()  # Get full connector catalog
"""

import sqlite3
from typing import List, Dict, Any
from models import NetRow, DesignatorRow, ConnectorRow, CableRow
from exceptions import DatabaseError

class SqliteDataSource:
    """
    Repository for SQLite database access.
    
    Provides methods to load data from the electrical design database.
    All methods return domain objects (dataclasses) rather than raw SQL results.
    
    Attributes:
        db_filepath: Path to the SQLite database file.
        
    Example:
        >>> db = SqliteDataSource("data/master.db")
        >>> if db.check_cable_existence("W001"):
        ...     connections = db.load_net_table("W001")
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
        Checks if a cable exists in the database.
        
        Useful for validating cable filters before generating YAML,
        avoiding errors from attempting to process non-existent cables.
        
        Args:
            cable_des: Cable designator to check (e.g., "W001").
            
        Returns:
            True if the cable has at least one connection in NetTable.
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
        """
        Loads connection data from NetTable.
        
        Retrieves point-to-point electrical connections. Each row represents
        a single wire connection between two pins via a specific cable.
        
        Args:
            cable_des_filter: Optional cable designator to filter results.
                            If empty, returns all connections in the database.
                            
        Returns:
            List of NetRow domain objects representing connections.
            
        Example:
            >>> nets = source.load_net_table("W001")
            >>> for net in nets:
            ...     print(f"{net.net_name}: {net.conn_des_1}:{net.pin_1} -> {net.conn_des_2}:{net.pin_2}")
        """
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
        """
        Loads the component-to-connector mapping table.
        
        Maps component designators to their physical connector part numbers.
        Essential for enriching connectors with catalog metadata.
        
        Returns:
            List of DesignatorRow objects with comp_des, conn_des, conn_mpn.
        """
        rows = self._fetch_dict_rows(self._build_query("DesignatorTable"))
        return [
            DesignatorRow(
                comp_des=row.get('comp_des'),
                conn_des=row.get('conn_des'),
                conn_mpn=row.get('conn_mpn')
            ) for row in rows
        ]

    def load_connector_table(self) -> List[ConnectorRow]:
        """
        Loads the connector catalog with part numbers and specifications.
        
        Contains manufacturer part numbers, pin counts, descriptions,
        and other metadata for all connectors used in the design.
        
        Returns:
            List of ConnectorRow objects with mpn, pincount, description, etc.
        """
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
        """
        Loads cable physical properties (gauge, length, notes).
        
        Contains the physical characteristics of cables such as wire gauge,
        length, and construction notes.
        
        Returns:
            List of CableRow objects with cable_des, wire_gauge, length, note.
        """
        rows = self._fetch_dict_rows(self._build_query("CableTable"))
        return [
            CableRow(
                cable_des=row.get('cable_des'),
                wire_gauge=row.get('wire_gauge'),
                length=row.get('length'),
                note=row.get('note')
            ) for row in rows
        ]
