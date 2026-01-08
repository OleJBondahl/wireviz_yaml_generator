"""
Main Entry Point for WireViz YAML Generator.

This script orchestrates the complete workflow from database to wiring diagrams:
1. Loads configuration from config.toml
2. Connects to SQLite database
3. Generates manufacturing attachments (BOM, Labels)
4. Creates WireViz YAML files
5. Invokes WireViz CLI to generate diagram images

Architecture:
    - Pure Core: Business logic is in transformations.py (pure functions)
    - Imperative Shell: This module handles I/O, subprocess calls, errors
    - Dependency Injection: WorkflowManager receives DataSource via constructor
    
Error Handling:
    All application errors are caught at this level and presented to the user.
    Uses sys.exit() only here (not in library code) for clean CLI behavior.

Example:
    Configure paths in config.toml, then:
    $ python src/main.py
"""

import sys
import shutil
import subprocess
from pathlib import Path
from typing import Set

from exceptions import WireVizError
from ReadConfig import ConfigLoader
from data_access import SqliteDataSource
from workflow_manager import WorkflowManager

def get_available_images(resource_path: Path) -> Set[str]:
    """
    Scans a directory for available connector image files.
    
    WireViz can embed images in diagrams. This function discovers
    which images are available so the transformation logic can
    reference them when building connector definitions.
    
    Args:
        resource_path: Directory containing connector image files (PNG).
        
    Returns:
        Set of image filenames (e.g., {"connector_x1.png", "terminal.png"}).
        Returns empty set if directory doesn't exist.
    """
    if not resource_path.is_dir():
        return set()
    return {f.name for f in resource_path.glob("*.png")}

def main() -> None:
    """
    Main workflow orchestration function.
    
    Executes the complete pipeline from database to diagrams:
    1. Loads configuration from config.toml
    2. Initializes database connection and workflow manager
    3. Scans for available connector images
    4. Generates manufacturing attachments (BOM and Labels)
    5. For each cable, generates YAML and invokes WireViz CLI
    
    Configuration:
        Edit constants in this function to control:
        - CREATE_BOM: Generate Bill of Materials
        - CREATE_LABELS: Generate wire/cable labels
        - CREATE_DRAWINGS: Generate diagram images
        - FROM_CABLE_NR, TO_CABLE_NR: Range of cables to process
        - DONT_INCLUDE_FILTER: Specific cables to skip
        
    Workflow:
        Attachments are generated once for all cables (BOM aggregates).
        YAML files and diagrams are generated per-cable (filtered).
        
    Raises:
        SystemExit: On any error (code 1), after printing error message.
    """
    try:
        # 1. Load Configuration
        config = ConfigLoader.get_instance()
        
        # Constants
        CREATE_BOM = True
        CREATE_LABELS = True
        CREATE_DRAWINGS = True
        FROM_CABLE_NR = 0
        TO_CABLE_NR = 50
        DONT_INCLUDE_FILTER = [10, 21, 32, 43]

        # 2. Initialize Dependencies
        db_source = SqliteDataSource(str(config.db_path))
        workflow = WorkflowManager(db_source)
        
        # 3. Prepare Environment
        # Scan images once (IO) -> Pass to logic (Pure)
        # Assuming resources are in parent of output path (legacy logic)
        resource_path = config.output_path.parent / "resources"
        available_images = get_available_images(resource_path)

        # 4. Build Filters
        cable_filters = [
            f"W{i:03d}"
            for i in range(FROM_CABLE_NR, TO_CABLE_NR + 1)
            if i not in DONT_INCLUDE_FILTER
        ]

        if not cable_filters:
            print("ℹ️  The 'cable_filters' list is empty. No diagrams will be generated.")
            return

        # 5. Execute Workflows
        
        # A. Attachments (BOM / Labels)
        workflow.run_attachment_workflow(
            cable_filters, 
            str(config.attachments_path),
            create_bom=CREATE_BOM, 
            create_labels=CREATE_LABELS
        )

        # B. Drawings (YAML + WireViz CLI)
        if CREATE_DRAWINGS:
            wireviz_executable = shutil.which("wireviz")
            if not wireviz_executable:
                # Log warning if the external tool is missing
                print("❌ 'wireviz' not found. Skipping diagram generation.")
            else:
                for cable_filter in cable_filters:
                    # Check existence
                    if not db_source.check_cable_existence(cable_filter):
                        print(f"   ⚠️ Skipping {cable_filter}. No data found.")
                        continue
                    
                    yaml_filepath = config.output_path / f"{cable_filter}.yaml"
                    
                    workflow.run_yaml_workflow(
                        cable_filter,
                        str(yaml_filepath),
                        available_images
                    )

                    # External CLI Call
                    command = [wireviz_executable, str(yaml_filepath), "--format", "s", "--output-dir", str(config.drawings_path)]
                    try:
                        subprocess.run(command, check=True, capture_output=True, text=True)
                        print(f"   ✅ Diagram generated for {cable_filter}")
                    except subprocess.CalledProcessError as e:
                        print(f"   ❌ WireViz Error for {cable_filter}: {e.stderr}")

    except WireVizError as e:
        print(f"❌ Application Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()