"""
Main script for generating wire harness documentation.

This script orchestrates the generation of wiring diagrams, Bills of Materials (BOMs),
and labels for a specified range of cables. It reads cable data from a
database, generates YAML files compatible with WireViz, and then invokes
the WireViz command-line tool to create the diagrams.

The script's behavior can be configured using the global options to enable or
disable the creation of BOMs, labels, and drawings, and to specify the
range of cable numbers to process.
"""


import InterfaceSqlYaml
import os
import subprocess
import shutil
from BuildFromSql import check_cable_existence # Import the new function
import ReadConfig
from BuildAttachments import create_bom, create_cablelabels, create_wirelabels
from typing import List




#----Options----
CREATE_BOM = True
CREATE_LABELS = True
CREATE_DRAWINGS = True

FROM_CABLE_NR = 0
TO_CABLE_NR = 50

#---------------


if __name__ == "__main__":
    
  DB_PATH = ReadConfig.DB_PATH
  OUTPUT_PATH = ReadConfig.OUTPUT_PATH
  DRAWINGS_PATH = ReadConfig.DRAWINGS_PATH
  ATTACHMENTS_PATH = ReadConfig.ATTACHMENTS_PATH
  

  # --- Cable Filter ---
  # Add the cable designators you want to generate diagrams for.
  # A separate YAML file will be created for each cable in this list.
  cable_filters = []
  dont_include_filter: List[int] = [10, 21, 32, 43]
  #Add cable x to y to filter
  X = FROM_CABLE_NR
  Y = TO_CABLE_NR
  for i in range(X, Y + 1):
    if i in dont_include_filter:
      continue
    cable_filters.append(f"W{i:03d}")

  if not cable_filters:
    print("ℹ️  The 'cable_filters' list is empty. No diagrams will be generated.")


  if CREATE_BOM:
    print("ℹ️  Creating BOM...")
    create_bom(DB_PATH, cable_filters, ATTACHMENTS_PATH)
    print("✅  BOM created.")
  
  if CREATE_LABELS:
    print("ℹ️  Creating LabelLists...")
    create_cablelabels(DB_PATH, cable_filters, ATTACHMENTS_PATH)
    create_wirelabels(DB_PATH, cable_filters, ATTACHMENTS_PATH)
    print("✅  LabelLists created.")



  if CREATE_DRAWINGS:
        # 1. Find the 'wireviz' executable
    wireviz_executable = shutil.which("wireviz")
    if not wireviz_executable:
        print("❌ 'wireviz' executable not found. Please install WireViz and ensure it's accessible from the command line.")
        exit(1)

    for cable_filter in cable_filters:
      # Check if the cable exists in the database before proceeding
      if not check_cable_existence(DB_PATH, cable_filter):
          print(f"   ⚠️ Skipping {cable_filter}. No data found for this cable in the database.")
          continue
        
      yaml_filepath = os.path.join(OUTPUT_PATH, f"{cable_filter}.yaml")

      InterfaceSqlYaml.sql_to_yaml(
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