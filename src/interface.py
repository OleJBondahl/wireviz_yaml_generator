#fetches data from choosen database, creates instances, calls yaml builder on instances
from sql_builder import *
from yaml_builder import build_yaml_file
import os


def sql_to_yaml(db_filepath: str, yaml_filepath: str, output_path: str, cable_des_filter: str = "") -> None:
  
  connector_data = db_to_connector_data(db_filepath, output_path, cable_des_filter=cable_des_filter)
  cable_data = db_to_cable_data(db_filepath, cable_des_filter=cable_des_filter)
  connection_data = db_to_connection_data(db_filepath, cable_des_filter=cable_des_filter)
  
  #call yaml builder
  build_yaml_file(
    connectors=connector_data,
    cables=cable_data,
    connections=connection_data,
    yaml_filepath=yaml_filepath,
  )


#test function
if __name__ == "__main__":

  # --- Robust Path Handling ---
  # Get the directory where the current script (`interface.py`) is located.
  script_dir = os.path.dirname(os.path.abspath(__file__))
  
  # Go one level up to the project's root directory.
  project_root = os.path.dirname(script_dir)
  
  # Construct absolute paths for the database and output file.
  # This ensures the correct files are always found.
  db_path = os.path.join(project_root, "data\master.db")
  output_path = os.path.join(project_root, "output\output.yaml")

  print(f"ℹ️  Script running from: {script_dir}")
  print(f"🔍 Looking for database at: {db_path}")

  # --- Component Filter ---
  # Set to a component designator (e.g., 'JB1') to only show connections to/from it.
  # Set to None to show all connections.
  comp_filter = "" # Example: 'JB1'

  sql_to_yaml(db_path, output_path, output_path, cable_des_filter="W1")
  