from typing import List, Dict, Any
from collections import defaultdict

#contains sql mapping functions, that convert sql keywords to yaml keywords

def map_connector_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maps raw SQL data to a list of connector dictionaries."""
    connectors = []
    # Create a lookup for mate information based on the main part number (mpn)
    mate_info_lookup = {row['mpn']: row for row in data if 'mate_mpn' in row and 'mpn' in row}
 
    # Process rows that represent a component connector
    for row in data:
        if 'comp_des' in row and 'conn_des' in row:
            connector = {
                'name': f"{row['comp_des']}_{row['conn_des']}",
                'pincount': row.get('pincount', 4)  # Use pincount from row, default to 4
            }
 
            # Find mate information if available
            conn_mpn = row.get('conn_mpn')
            if conn_mpn and conn_mpn in mate_info_lookup:
                mate_info = mate_info_lookup[conn_mpn]
                connector['pincount'] = mate_info.get('pincount', connector['pincount'])
                if 'mate_mpn' in mate_info:
                    connector['mpn'] = mate_info['mate_mpn']
 
            connectors.append(connector)
 
    return connectors

def map_cable_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

  bundle_data: List[Dict[str, Any]] = []
  for row in data:
    bundle_row = {}
    bundle_row['cable_des'] = row['comp_des_1'] + "_" + row['conn_des_1'] + "_" + row['comp_des_2'] + "_" + row['conn_des_2']
    bundle_row['wirelabels'] = row['net_name']
    bundle_data.append(bundle_row)


  #Now we have a List[Dict[str,str]] with alot of identical keywords. we want to komibne these identical keywords, so that we get List[Dict[str,List[str]]] with all the values added to a list.
  aggregated_data = defaultdict(list)
  for bundle_row in bundle_data:
    cable_des = bundle_row['cable_des']
    wirelabels = bundle_row['wirelabels']
    aggregated_data[cable_des].append(wirelabels)

  final_data = []
  for cable_des, wirelabels in aggregated_data.items():
    final_data.append({
      'name': cable_des,
      'wirelabels': wirelabels,
      'wirecount': len(wirelabels)  # Eksplisitt sett wirecount
    })

  return final_data


def map_connection_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  mapped_data: List[Dict[str, Any]] = []
  cable_pin_counters = defaultdict(int)
  
  for row in data:
    mapped_row = {}
    from_name = row['comp_des_1'] + "_" + row['conn_des_1']
    from_pin = row['pin_1']
    to_name = row['comp_des_2'] + "_" + row['conn_des_2']
    to_pin = row['pin_2']
    via_name = row['comp_des_1'] + "_" + row['conn_des_1'] + "_" + row['comp_des_2'] + "_" + row['conn_des_2']
    cable_pin_counters[via_name] += 1
    via_pin = cable_pin_counters[via_name]
    
    # Create a list representing one full connection path
    connection_nodes = [{from_name: from_pin}, {via_name: via_pin}, {to_name: to_pin}]
    
    # Wrap the nodes in a dictionary that matches the new Connection dataclass
    mapped_row = {'nodes': connection_nodes}
    mapped_data.append(mapped_row)

  return mapped_data

    

    
    