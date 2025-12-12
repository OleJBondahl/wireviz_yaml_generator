"""
Excel Output Adapter.

This module handles writing list-of-dictionary data structures to 
Excel (.xlsx) files using pandas. It isolates the dependency on 
pandas and file I/O from the core logic.
"""

import pandas as pd
import os
import csv
from typing import List, Dict, Any

def write_xlsx(data: List[Dict[str, Any]], filename: str, output_path: str) -> None:
    """
    Writes a list of dictionaries to an Excel file.

    Args:
        data: List of dicts, where each dict key becomes a column header.
        filename: Base name of the file (without extension).
        output_path: Directory to write the file to.
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
    Reads miscellaneous items (screws, tape, etc.) from a CSV file 
    and appends them to the BOM list.

    Args:
        bom_data: Existing generated BOM data.
        filename: Filename of the CSV containing misc items.
        output_path: Directory where the CSV is located.

    Returns:
        List[Dict[str, Any]]: A new list combined of generated + misc items.
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
