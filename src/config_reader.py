import tomllib
import os

  
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
CONFIG_FILE =  os.path.join(project_root, "config.toml")

def load_config():
    try:
        with open(CONFIG_FILE, mode="rb") as fp:
            config = tomllib.load(fp)
        return config
    except FileNotFoundError:
        print(f"ERROR: Konfigurasjonsfilen ble ikke funnet på: {CONFIG_FILE}")
        return {}

CONFIG = load_config()

BASE_PATH = CONFIG.get("base_repo_path")
DB_RELATIVE_PATH = CONFIG.get("db_path")
OUTPUT_RELATIVE_DIR = CONFIG.get("output_path")
DRAWINGS_RELATIVE_DIR = CONFIG.get("drawings_path")

DB_PATH = os.path.join(BASE_PATH, DB_RELATIVE_PATH)
OUTPUT_PATH = os.path.join(BASE_PATH, OUTPUT_RELATIVE_DIR)
DRAWINGS_PATH = os.path.join(BASE_PATH, DRAWINGS_RELATIVE_DIR)

