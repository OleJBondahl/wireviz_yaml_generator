import tomllib
from pathlib import Path
import sys

  
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent
CONFIG_FILE = project_root / "config.toml"

def load_config():
    try:
        with open(CONFIG_FILE, mode="rb") as fp:
            config = tomllib.load(fp)
        return config
    except FileNotFoundError:
        print(f"❌ ERROR: Configuration file not found at: {CONFIG_FILE}")
        sys.exit(1)

CONFIG = load_config()

def get_config_value(key: str):
    """Gets a value from the config or exits if it's missing."""
    value = CONFIG.get(key)
    if value is None:
        print(f"❌ ERROR: Configuration key '{key}' not found in {CONFIG_FILE}")
        sys.exit(1)
    return value

BASE_PATH = get_config_value("base_repo_path")
DB_RELATIVE_PATH = get_config_value("db_path")
OUTPUT_RELATIVE_DIR = get_config_value("output_path")
DRAWINGS_RELATIVE_DIR = get_config_value("drawings_path")

DB_PATH = Path(BASE_PATH) / DB_RELATIVE_PATH
OUTPUT_PATH = Path(BASE_PATH) / OUTPUT_RELATIVE_DIR
DRAWINGS_PATH = Path(BASE_PATH) / DRAWINGS_RELATIVE_DIR
