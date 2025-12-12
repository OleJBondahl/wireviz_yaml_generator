"""
Configuration Loader.

This module loads global settings from `config.toml`.
It provides typesafe access to paths for the Database, Output, 
and Template directories.
"""

import tomllib
from pathlib import Path
from typing import Any, Dict, Optional
from exceptions import ConfigurationError

# Define paths relative to this script
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.toml"

class ConfigLoader:
    """
    Handles loading and accessing configuration settings.
    Initialized explicitly to make testing easier (avoids import side-effects).
    """
    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> 'ConfigLoader':
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = ConfigLoader()
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Loads the configuration from file."""
        try:
            with open(CONFIG_FILE, mode="rb") as fp:
                self._config = tomllib.load(fp)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found at: {CONFIG_FILE}")

    def get_value(self, key: str) -> Any:
        """
        Retrieves a specific value from the configuration.
        
        Raises:
            ConfigurationError: If key is missing.
        """
        value = self._config.get(key)
        if value is None:
            raise ConfigurationError(f"Configuration key '{key}' not found in {CONFIG_FILE}")
        return value

    @property
    def base_path(self) -> Path:
        return Path(str(self.get_value("base_repo_path")))

    @property
    def db_path(self) -> Path:
        return self.base_path / str(self.get_value("db_path"))

    @property
    def output_path(self) -> Path:
        return self.base_path / str(self.get_value("output_path"))

    @property
    def drawings_path(self) -> Path:
        return self.base_path / str(self.get_value("drawings_path"))

    @property
    def attachments_path(self) -> Path:
        return self.base_path / str(self.get_value("attachments_path"))
