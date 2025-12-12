"""
Custom Exceptions for the WireViz YAML Generator.

These exceptions consolidate error handling, allowing the main application
to decide how to present errors to the user (CLI print, log, GUI dialog, etc.)
without low-level modules forcefully exiting the process.
"""

class WireVizError(Exception):
    """Base class for all application-specific exceptions."""
    pass

class ConfigurationError(WireVizError):
    """Raised when configuration is missing or invalid."""
    pass

class DatabaseError(WireVizError):
    """Raised when the database cannot be accessed or queried."""
    pass
