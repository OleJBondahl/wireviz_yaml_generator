"""Data Source Protocol — structural interface for data providers."""

from typing import Protocol

from .models import CableRow, ConnectorRow, DesignatorRow, NetRow


class DataSourceProtocol(Protocol):
    """Structural interface shared by SqliteDataSource and CsvDataSource."""

    def check_cable_existence(self, cable_des: str) -> bool: ...

    def load_net_table(self, cable_des_filter: str = "") -> list[NetRow]: ...

    def load_designator_table(self) -> list[DesignatorRow]: ...

    def load_connector_table(self) -> list[ConnectorRow]: ...

    def load_cable_table(self) -> list[CableRow]: ...
