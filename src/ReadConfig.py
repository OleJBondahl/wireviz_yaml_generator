"""
Configuration Loader.

This module provides centralized configuration management for the WireViz YAML Generator.
It loads settings from a TOML configuration file and provides type-safe access to 
file paths for the database, output directories, and drawing locations.

The ConfigLoader uses the Singleton pattern to ensure configuration is loaded once
and shared across the application, avoiding redundant file I/O and ensuring consistency.

Example:
    >>> from ReadConfig import ConfigLoader
    >>> config = ConfigLoader.get_instance()
    >>> db_path = config.db_path
    >>> print(f"Database location: {db_path}")

Design Pattern:
    - Singleton: Ensures only one configuration instance exists
    - Lazy Loading: Configuration is loaded on first access
    - Type Safety: Returns Path objects for all filesystem locations
"""

import tomllib
from pathlib import Path
from typing import Any, Dict, Optional
from exceptions import ConfigurationError

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.toml"

class ConfigLoader:
    """
    Singleton configuration manager for application settings.
    
    This class reads the config.toml file and provides property-based access
    to configuration values. It ensures that configuration is loaded exactly once
    and validates that all required keys are present.
    
    Attributes:
        _instance: Singleton instance (class variable)
        _config: Dictionary containing loaded configuration values
    
    Example:
        >>> config = ConfigLoader.get_instance()
        >>> output_dir = config.output_path
        >>> db_file = config.db_path
    """
    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> 'ConfigLoader':
        """
        Returns the singleton instance of ConfigLoader.
        
        Creates and initializes the instance on first call, then returns
        the same instance on subsequent calls.
        
        Returns:
            ConfigLoader: The singleton configuration instance.
            
        Raises:
            ConfigurationError: If config file is missing or invalid.
        """
        if cls._instance is None:
            cls._instance = ConfigLoader()
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Loads configuration from the TOML file.
        
        Reads the config.toml file from the project root and parses it
        into the internal _config dictionary.
        
        Raises:
            ConfigurationError: If the configuration file is not found.
        """
        try:
            with open(CONFIG_FILE, mode="rb") as fp:
                self._config = tomllib.load(fp)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found at: {CONFIG_FILE}")

    def get_value(self, key: str) -> Any:
        """
        Retrieves a configuration value by key.
        
        Args:
            key: The configuration key to retrieve (e.g., "db_path").
        
        Returns:
            The value associated with the key (type depends on config).
        
        Raises:
            ConfigurationError: If the key is not found in the configuration.
        """
        value = self._config.get(key)
        if value is None:
            raise ConfigurationError(f"Configuration key '{key}' not found in {CONFIG_FILE}")
        return value

    @property
    def base_path(self) -> Path:
        """
        Returns the base repository path.
        
        This is the root directory where all relative paths are anchored.
        Typically points to the parent project that contains the data and outputs.
        
        Returns:
            Path: Absolute path to the base repository directory.
        """
        return Path(str(self.get_value("base_repo_path")))

    @property
    def db_path(self) -> Path:
        """
        Returns the full path to the SQLite database file.
        
        Returns:
            Path: Absolute path to the master.db database file.
        """
        return self.base_path / str(self.get_value("db_path"))

    @property
    def output_path(self) -> Path:
        """
        Returns the directory where YAML files are generated.
        
        Returns:
            Path: Absolute path to the YAML output directory.
        """
        return self.base_path / str(self.get_value("output_path"))

    @property
    def drawings_path(self) -> Path:
        """
        Returns the directory where WireViz generates diagram images.
        
        Returns:
            Path: Absolute path to the drawings output directory (PNG/SVG files).
        """
        return self.base_path / str(self.get_value("drawings_path"))

    @property
    def attachments_path(self) -> Path:
        """
        Returns the directory where manufacturing attachments are generated.
        
        This includes BOM (Bill of Materials) Excel files and label lists.
        
        Returns:
            Path: Absolute path to the attachments output directory.
        """
        return self.base_path / str(self.get_value("attachments_path"))
