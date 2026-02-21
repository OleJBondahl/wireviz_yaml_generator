"""
WireViz YAML Generator.

A tool for generating WireViz YAML files and manufacturing documentation
from SQLite electrical design databases.
"""

__version__ = "0.1.0"
__author__ = "Ole Johan Bondahl"
__license__ = "MIT"

from .models import (
    Connector,
    Cable,
    Connection,
    BomItem,
    Wire,
    NetRow,
    DesignatorRow,
    ConnectorRow,
    CableRow,
)

from .exceptions import (
    WireVizError,
    ConfigurationError,
    DatabaseError,
    DataSourceError,
)

from .protocols import DataSourceProtocol
from .csv_data_source import CsvDataSource
from .workflow_manager import WorkflowManager

__all__ = [
    "Connector",
    "Cable",
    "Connection",
    "BomItem",
    "Wire",
    "NetRow",
    "DesignatorRow",
    "ConnectorRow",
    "CableRow",
    "WireVizError",
    "ConfigurationError",
    "DatabaseError",
    "DataSourceError",
    "DataSourceProtocol",
    "CsvDataSource",
    "WorkflowManager",
]
