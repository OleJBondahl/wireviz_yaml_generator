from typing import List, Dict, Any
from sql_data_loader import fetch_table
import re


def _natural_sort_key(s: str):
    """
    Create a sort key for natural sorting (e.g., 'J10' comes after 'J2').
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]


def db_to_connector_data(db_filepath: str, comp_des_filter: str = None) -> List[Dict[str, Any]]:
  designator_table = fetch_table("DesignatorTable", db_filepath)
  connector_table = fetch_table("ConnectorTable", db_filepath)

  # If filtering, determine the set of required connectors from the filtered NetTable
  required_connectors = set()
  if comp_des_filter:
    where_clause = f"comp_des_1 = '{comp_des_filter}' OR comp_des_2 = '{comp_des_filter}'"
    filtered_net_table = fetch_table("NetTable", db_filepath, where_clause=where_clause)
    for row in filtered_net_table:
      required_connectors.add(f"{row['comp_des_1']}-{row['conn_des_1']}")
      required_connectors.add(f"{row['comp_des_2']}-{row['conn_des_2']}")
    
    # Filter the designator table to only include required connectors
    designator_table = [
        row for row in designator_table 
        if f"{row['comp_des']}-{row['conn_des']}" in required_connectors
    ]

  # Sort the (potentially filtered) data by comp_des, then naturally by conn_des
  designator_table.sort(key=lambda x: (_natural_sort_key(x['comp_des']), _natural_sort_key(x['conn_des'])))

  conn_data: List[Dict[str, Any]] = []
  for row in designator_table:
    conn_row = {}
    conn_row['name'] = f"{row['comp_des']}-{row['conn_des']}"
    conn_row['conn_mpn'] = row['conn_mpn']
    conn_data.append(conn_row)

  # Create a lookup map for faster access to connector table data
  connector_table_map = {row['mpn']: row for row in connector_table}

  # Add mate info from connector table to conn_data
  for conn_row in conn_data:
    conn_mpn = conn_row.get('conn_mpn')
    if conn_mpn and conn_mpn in connector_table_map:
      mate_info = connector_table_map[conn_mpn]
      conn_row['pincount'] = mate_info['pincount']
      conn_row['mpn'] = mate_info['mate_mpn']
    else:
      # If no match is found, provide default values to prevent it from being deleted
      print(f"⚠️  Warning: MPN '{conn_mpn}' for connector '{conn_row['name']}' not found in ConnectorTable. Using default values.")
      conn_row['pincount'] = 99  # Default value
      conn_row['mpn'] = 'NotFound' # Default value
      conn_row['hide_disconnected_pins'] = True

  for conn in conn_data:
    conn.pop('conn_mpn', None)
  return conn_data


def _get_sorted_unique_cable_names(net_table: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts unique cable names from the net_table and sorts them using natural sorting
    on the component and connector designators. This ensures a consistent order.
    """
    # First, sort the entire table to establish a definitive order.
    net_table.sort(key=lambda x: (_natural_sort_key(x['comp_des_1']), _natural_sort_key(x['conn_des_1']), _natural_sort_key(x['comp_des_2']), _natural_sort_key(x['conn_des_2'])))
    
    # Then, extract unique cable names while preserving that order.
    seen = set()
    unique_names = []
    for row in net_table:
        name = f"{row['comp_des_1']}_{row['conn_des_1']}_{row['comp_des_2']}_{row['conn_des_2']}"
        if name not in seen:
            seen.add(name)
            unique_names.append(name)
    return unique_names


def db_to_cable_data(db_filepath: str, comp_des_filter: str = None) -> List[Dict[str, Any]]:
  where_clause = None
  if comp_des_filter:
    # Select rows where the component is on either side of the connection
    where_clause = f"comp_des_1 = '{comp_des_filter}' OR comp_des_2 = '{comp_des_filter}'"
  
  net_table = fetch_table("NetTable", db_filepath, where_clause=where_clause)

  cable_data: List[Dict[str, Any]] = []
  for row in net_table:
    cable_row = {}
    cable_row['cable_des'] = f"{row['comp_des_1']}_{row['conn_des_1']}_{row['comp_des_2']}_{row['conn_des_2']}"
    cable_row['wirelabels'] = row['net_name']
    cable_data.append(cable_row)
  
  #remove duplicates and aggregate wirelabels
  aggregated_data = {}
  for cable in cable_data:
    name = cable['cable_des']
    wirelabel = cable['wirelabels']
    if name not in aggregated_data:
      aggregated_data[name] = {
        'name': name,
        'wirelabels': [],
      }
    aggregated_data[name]['wirelabels'].append(wirelabel)
  cable_data = list(aggregated_data.values())

  #set wirecount
  for cable in cable_data:
    cable['wirecount'] = len(cable['wirelabels'])
    cable['length'] = 100  # Default length
    cable['length_unit'] = 'mm'  # Default length unit
    cable['gauge'] = 0.5  # Default gauge
    cable['gauge_unit'] = 'mm2'  # Default gauge unit
    cable['color'] = 'WH' # Default color
  
  # Get the canonical sorted list of cable names
  sorted_cable_names = _get_sorted_unique_cable_names(net_table)
  cable_data.sort(key=lambda x: sorted_cable_names.index(x['name']))

  #rename cable_des to W1, W2, ...
  for i, cable in enumerate(cable_data):
    cable['name'] = f"W{i+1}"
  
  
  
  return cable_data


def db_to_connection_data(db_filepath: str, comp_des_filter: str = None) -> List[Dict[str, Any]]:
  where_clause = None
  if comp_des_filter:
    # Select rows where the component is on either side of the connection
    where_clause = f"comp_des_1 = '{comp_des_filter}' OR comp_des_2 = '{comp_des_filter}'"

  net_table = fetch_table("NetTable", db_filepath, where_clause=where_clause)

  connection_data: List[Dict[str, Any]] = []
  cable_pin_counters = {}

  for row in net_table:
    connection_row = {}
    from_name = f"{row['comp_des_1']}-{row['conn_des_1']}"
    to_name = f"{row['comp_des_2']}-{row['conn_des_2']}"
    via_name = f"{row['comp_des_1']}_{row['conn_des_1']}_{row['comp_des_2']}_{row['conn_des_2']}"

    # Manage pin numbering for cables
    if via_name not in cable_pin_counters:
      cable_pin_counters[via_name] = 0
    cable_pin_counters[via_name] += 1
    via_pin = cable_pin_counters[via_name]

    connection_row['from_name'] = from_name
    connection_row['from_pin'] = row['pin_1']
    connection_row['to_name'] = to_name
    connection_row['to_pin'] = row['pin_2']
    connection_row['via_name'] = via_name
    connection_row['via_pin'] = via_pin

    connection_data.append(connection_row)
  
  # Create a mapping from the original cable name ('via_name') to the new 'W' name.
  # This ensures connections are grouped correctly under the same cable.
  # Use the canonical sorting function to guarantee order matches the cable definitions.
  unique_via_names = _get_sorted_unique_cable_names(net_table)
  cable_name_map = {name: f"W{i+1}" for i, name in enumerate(unique_via_names)}

  # Use the map to assign the correct 'W' name to each connection.
  for connection in connection_data:
    connection['name'] = cable_name_map[connection['via_name']]

  return connection_data