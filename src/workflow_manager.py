"""
Workflow Manager.

This module unifies the orchestration of the application.
It acts as the single entry point for high-level business logic,
handling Data Loading, Filtering, and delegating to specific workflows
(Attachment Generation vs YAML Generation).

It supports Dependency Injection for the Data Source.
"""

from typing import Set, List
from data_access import SqliteDataSource
from models import NetRow, CableRow, ConnectorRow, DesignatorRow
import transformations
import BuildYaml
import excel_writer

class WorkflowManager:
    def __init__(self, data_source: SqliteDataSource):
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
        Generates BOM and Labels for a list of cables.
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
        Generates a single WireViz YAML file for the specified cable.
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
