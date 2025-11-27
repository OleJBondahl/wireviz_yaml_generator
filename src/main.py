import interface
import os
import subprocess
import shutil
from sql_builder import check_cable_existence # Import the new function
import config_reader


if __name__ == "__main__":
    
  DB_PATH = config_reader.DB_PATH
  OUTPUT_PATH = config_reader.OUTPUT_PATH
  DRAWINGS_PATH = config_reader.DRAWINGS_PATH

  # 1. Find the 'wireviz' executable
  wireviz_executable = shutil.which("wireviz")
  if not wireviz_executable:
      print("❌ 'wireviz' executable not found. Please install WireViz and ensure it's accessible from the command line.")
      exit(1)

  # --- Cable Filter ---
  # Add the cable designators you want to generate diagrams for.
  # A separate YAML file will be created for each cable in this list.
  cable_filters = []
  #Add cable x to y to filter
  X = 1
  Y = 44
  for i in range(X, Y + 1):
    cable_filters.append(f"W{i:03d}")

  if not cable_filters:
    print("ℹ️  The 'cable_filters' list is empty. No diagrams will be generated.")

  for cable_filter in cable_filters:
    # Check if the cable exists in the database before proceeding
    if not check_cable_existence(DB_PATH, cable_filter):
        print(f"   ⚠️ Skipping {cable_filter}. No data found for this cable in the database.")
        continue

    yaml_filepath = os.path.join(OUTPUT_PATH, f"{cable_filter}.yaml")

    interface.sql_to_yaml(
        db_filepath=DB_PATH,
        yaml_filepath=yaml_filepath,
        output_path=OUTPUT_PATH,
        cable_des_filter=cable_filter
    )
    
    command = [wireviz_executable, yaml_filepath, "--format", "s", "--output-dir",DRAWINGS_PATH]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"   ✅ Diagram successfully generated for {cable_filter}.yaml")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error running wireviz for {cable_filter}.yaml:")
        print(f"      {e.stderr}")