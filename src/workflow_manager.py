"""
Workflow Manager - Application Orchestration.

This module coordinates the high-level business workflows of the application.
It acts as an intermediary between the entry point (main.py) and the pure
transformation logic (transformations.py), orchestrating data loading, filtering,
and output generation.

Workflows:
    1. Attachment Workflow: Generates BOM and Labels (Excel files)
    2. YAML Workflow: Generates WireViz YAML for individual cables

Design Pattern:
    - Dependency Injection: Receives DataSource via constructor
    - Separation of Concerns: Orchestrates but doesn't transform
    - Single Responsibility: Coordinates workflows, delegates actual work

Architecture:
    main.py -> WorkflowManager -> transformations.py
           └-> data_access.py
           └-> BuildYaml.py / excel_writer.py
"""

from typing import Set, List
from data_access import SqliteDataSource
from models import NetRow, CableRow, ConnectorRow, DesignatorRow
import transformations
import BuildYaml
import excel_writer

class WorkflowManager:
    """
    Orchestrates application workflows using dependency injection.
    
    This class manages the complete data pipeline from loading database
    tables through transformation to output generation. It handles filtering
    logic and coordinates between multiple subsystems.
    
    Attributes:
        _source: Injected data source for database access.
        
    Example:
        >>> db = SqliteDataSource("data/master.db")
        >>> workflow = WorkflowManager(db)
        >>> workflow.run_attachment_workflow(["W001", "W002"], "output/")
    """
    def __init__(self, data_source: SqliteDataSource):
        """
        Initializes the workflow manager with a data source.
        
        Args:
            data_source: Repository providing access to the electrical design database.
        """
        self._source = data_source

    def _load_and_filter_data(self, cable_des_filter: str = ""):
        """
        Internal helper: Loads all required tables and filters NetTable
        based on the cable designator.
        """
        net_rows = self._source.load_net_table(cable_des_filter)
        connector_rows = self._source.load_connector_table()
        designator_rows = self._source.load_designator_table()
        cable_rows = self._source.load_cable_table()
        
        return net_rows, connector_rows, designator_rows, cable_rows

    def run_attachment_workflow(
        self, 
        cable_filters: List[str], 
        output_path: str,
        create_bom: bool = True,
        create_labels: bool = True
    ) -> None:
        """
        Generates manufacturing attachments (BOM and Labels) for specified cables.
        
        This workflow creates Excel files for manufacturing and assembly:
        - BOM (Bill of Materials): Consolidated parts list with quantities
        - Cable Labels: Cut-list with cable designators and lengths
        - Wire Labels: End-point labels showing connection information
        
        The BOM aggregates all components across the specified cables,
        so filtering affects which cables contribute to the BOM.
        
        Args:
            cable_filters: List of cable designators to include (e.g., ["W001", "W002"]).
            output_path: Directory where Excel files will be written.
            create_bom: Whether to generate the Bill of Materials.
            create_labels: Whether to generate cable and wire label lists.
            
        Example:
            >>> workflow.run_attachment_workflow(
            ...     cable_filters=["W001", "W002", "W003"],
            ...     output_path="attachments/",
            ...     create_bom=True,
            ...     create_labels=True
            ... )
        """
        # Load all data upfront to ensure complete coverage for BOM generation.
        # This approach avoids partial data loading issues when cables interact.
        
        all_net_rows = self._source.load_net_table()
        # Filter Logic
        net_rows = [r for r in all_net_rows if r.cable_des in cable_filters]
        cable_rows_filtered = [r for r in self._source.load_cable_table() if r.cable_des in cable_filters]
        
        # Load others fully
        connector_rows = self._source.load_connector_table()
        designator_rows = self._source.load_designator_table()

        if create_bom:
            print("ℹ️  Creating BOM...")
            bom_data = transformations.generate_bom_data(
                net_rows=net_rows,
                designator_rows=designator_rows,
                connector_rows=connector_rows,
                cable_rows=cable_rows_filtered
            )
            bom_data = excel_writer.add_misc_bom_items(bom_data, "MiscBOM", output_path)
            excel_writer.write_xlsx(bom_data, "BOM", output_path)
            print("✅  BOM created.")

        if create_labels:
            print("ℹ️  Creating LabelLists...")
            cable_labels = transformations.generate_cable_labels(net_rows)
            wire_labels = transformations.generate_wire_labels(net_rows)
            
            excel_writer.write_xlsx(cable_labels, "Cablelabels", output_path)
            excel_writer.write_xlsx(wire_labels, "WireLabels", output_path)
            print("✅  LabelLists created.")

    def run_yaml_workflow(
        self,
        cable_filter: str,
        yaml_filepath: str,
        available_images: Set[str]
    ) -> None:
        """
        Generates a WireViz YAML file for a single cable.
        
        This workflow:
        1. Loads all database tables filtered by cable designator
        2. Transforms data into domain objects (Connectors, Cables, Connections)
        3. Builds and writes a YAML file compatible with WireViz
        
        The generated YAML can then be passed to the WireViz CLI tool
        to create visual wiring diagram images.
        
        Args:
            cable_filter: Single cable designator (e.g., "W001").
            yaml_filepath: Full path where YAML file should be written.
            available_images: Set of image filenames available for connector images.
            
        Example:
            >>> images = {"terminal.png", "connector_x1.png"}
            >>> workflow.run_yaml_workflow(
            ...     cable_filter="W001",
            ...     yaml_filepath="output/W001.yaml",
            ...     available_images=images
            ... )
        """
        # Load & Filter
        net_rows, connector_rows, designator_rows, cable_rows = self._load_and_filter_data(cable_filter)
        
        # Transform
        connector_data = transformations.process_connectors(
            net_rows=net_rows,
            designator_rows=designator_rows,
            connector_rows=connector_rows,
            available_images=available_images,
            filter_active=True
        )

        cable_data = transformations.process_cables(
            net_rows=net_rows,
            cable_rows=cable_rows
        )

        connection_data = transformations.process_connections(
            net_rows=net_rows
        )

        # Build View
        BuildYaml.build_yaml_file(
            connectors=connector_data,
            cables=cable_data,
            connections=connection_data,
            yaml_filepath=yaml_filepath
        )
