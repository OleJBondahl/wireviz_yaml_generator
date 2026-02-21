"""
Excel Output Adapter.

This module handles writing structured data to Excel (.xlsx) files using pandas.
It serves as an adapter layer isolating the core business logic from the pandas
library and file I/O operations, following the Dependency Inversion Principle.

Design Philosophy:
    - Separation of Concerns: Core logic doesn't know about Excel or pandas
    - Simple Interface: Accepts list-of-dict (universal tabular format)
    - Error Handling: Gracefully handles empty data and missing files
    
Data Format:
    Functions expect data as: List[Dict[str, Any]]
    Example:
        [
            {"MPN": "123-456", "Description": "Connector", "Quantity": 5},
            {"MPN": "789-012", "Description": "Wire", "Quantity": 100}
        ]
    Each dict represents a row, keys become column headers.

Example:
    >>> bom_data = [{"MPN": "X123", "Qty": 10}]
    >>> write_xlsx(bom_data, "BOM", "output/")
"""

import pandas as pd
import os
import csv
from typing import List, Dict, Any

def write_xlsx(data: List[Dict[str, Any]], filename: str, output_path: str) -> None:
    """
    Writes a list of dictionaries to an Excel file.
    
    Each dictionary represents a row, and dictionary keys become column headers.
    If the data list is empty, prints a warning and skips file creation.

    Args:
        data: List of dictionaries where each dict is a row of data.
              Keys are column names, values are cell values.
        filename: Base name for the output file (without .xlsx extension).
        output_path: Directory path where the file will be written.
        
    Example:
        >>> data = [
        ...     {"Part": "Connector", "Quantity": 5},
        ...     {"Part": "Wire", "Quantity": 100}
        ... ]
        >>> write_xlsx(data, "BOM", "attachments/")
    """
    if not data:
        print(f"⚠️ Warning: No data to write for {filename}")
        return

    output_file = os.path.join(output_path, f"{filename}.xlsx")
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)


def add_misc_bom_items(
    bom_data: List[Dict[str, Any]], 
    filename: str, 
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Appends miscellaneous BOM items from a CSV file to generated BOM data.
    
    This function allows adding manual BOM entries (screws, cable ties, labels, etc.)
    that aren't auto-generated from the database. The CSV file should have the same
    column structure as the generated BOM (MPN, Description, Quantity, etc.).
    
    If the CSV file doesn't exist, returns the original BOM data unchanged with a warning.

    Args:
        bom_data: Existing auto-generated BOM entries (list of dictionaries).
        filename: Base name of the CSV file containing manually-added items.
        output_path: Directory where the CSV file is located.

    Returns:
        Combined list containing both generated and manually-added BOM items.
        
    Example:
        >>> generated_bom = [{"MPN": "CON123", "Quantity": 5}]
        >>> full_bom = add_misc_bom_items(generated_bom, "MiscBOM", "attachments/")
        >>> # Returns original BOM + items from attachments/MiscBOM.csv
    """
    csv_file_path = os.path.join(output_path, f"{filename}.csv")
    
    if not os.path.exists(csv_file_path):
        print(f"⚠️ Warning: Misc BOM file not found at {csv_file_path}")
        return bom_data

    misc_data = []
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as csv_file: # utf-8-sig handles BOM characters
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            misc_data.append(row)
    
    return bom_data + misc_data
