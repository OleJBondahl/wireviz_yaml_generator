import interface
import os
import subprocess
import shutil
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

  comp_filter = ['JB1', 'JB2', 'JB3', 'JB4', None, 'BMU1', 'BMU2', 'BMU3', 'BMU4']

  for filter in comp_filter:
    output_filename_base = filter if filter else 'all'
    yaml_filepath = os.path.join(OUTPUT_PATH, f"{output_filename_base}.yaml")

    interface.sql_to_yaml(
        db_filepath=DB_PATH,
        yaml_filepath=yaml_filepath,
        comp_des_filter=filter  # Example: 'JB1'
    )

    # 2. Build the command as a list of strings.
    # Each argument is a separate element in the list.
    # This command is equivalent to: `wireviz "path/to/file.yaml" --output-formats svg`
    command = [wireviz_executable, yaml_filepath, "--format", "s", "--output-dir",DRAWINGS_PATH]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"   ✅ Diagram successfully generated for {output_filename_base}.yaml")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error running wireviz for {output_filename_base}.yaml:")
        print(f"      {e.stderr}")