from typing import List, Dict, Any
from LoadFromSql import fetch_table





'''
Builds BOM and label list for the entire list of cables
Output xlsx files

BOM layout:
Description, mpn, manufacturer, quantity, unit 

Types of bom rows:
Connectors
Pins
Wires
Misc (get from misc csv file)
'''

def db_to_BOM(db_filepath: str, cable_des_filter: List[str]):
  #Load from sql, filter out rows by cable_des_filter
  net_table = fetch_table("NetTable", db_filepath)
  cable_table = fetch_table("CableTable", db_filepath)
  component_table = fetch_table("ComponentTable", db_filepath)
  connector_table = fetch_table("ConnectorTable", db_filepath)
  designator_table = fetch_table("DesignatorTable", db_filepath)  

  if cable_des_filter:
    net_table = [row for row in net_table if row['cable_des'] in cable_des_filter]
    cable_table = [row for row in cable_table if row['cable_des'] in cable_des_filter]
  
  #build List[dict] for connectors
  #Dict{mpn: , description: , quantity: , unit:pcs}
  #mpn = net_table-> get set(conn_des) -> set(conn_des) -> get designator table mpn, increment counter -> set(mpn) -> connector_table mate_mpn, set dict_row(mpn: mate_mpn)
  #description = connector_table description of mpn (after mpn is set)
  #quantity = designator_table number of mpn instances (set.add(mpn) if exists, increment counter
  bom_data: List[Dict[str, Any]] = []

  conn_set = set()
  for row in net_table:
    conn_des_1 = row['comp_des_1'] + '-' + row['conn_des_1']
    conn_des_2 = row['comp_des_2'] + '-' + row['conn_des_2']
    conn_set.add(conn_des_1)
    conn_set.add(conn_des_2)
  
  part_counter: Dict[str, int] = {}
  for row in designator_table:
    conn_des = row['comp_des'] + '-' + row['conn_des']
    if conn_des in conn_set:
      comp_mpn = row['conn_mpn']
      part_counter[comp_mpn] = part_counter.get(comp_mpn, 0) + 1 # This counts the number of times a specific MPN appears in the designator table for the selected connectors.

  for row in connector_table:
    for mpn in part_counter:
      if row['mpn'] == mpn:
        dict_row = {}
        dict_row['mpn'] = row['mate_mpn']
        dict_row['description'] = row['description']
        dict_row['manufacturer'] = row['manufacturer']
        dict_row['quantity'] = part_counter[mpn]
        dict_row['unit'] = 'pcs'
        bom_data.append(dict_row)
  

  #build List[dict] for wires
  wire_data: List[Dict[str, Any]] = []
  wire_counter: Dict[str, int] = {}
  for row in net_table:
    if "24V" in row['net_name']:
      wire_counter[row['cable_des'] +"Red"] = wire_counter.get(row['cable_des'], 0) + 1
    elif "gnd" in row['net_name']:
      wire_counter[row['cable_des'] +"Black"] = wire_counter.get(row['cable_des'], 0) + 1
    else:
      wire_counter[row['cable_des'] +"White"] = wire_counter.get(row['cable_des'], 0) + 1
  
  MANUFACTURER = ""
  DESCRIPTION = "Radox 125"
  UNIT = "Meter"
  for row in cable_table:
    
    if wire_counter.get(row['cable_des'] +"Red",0) > 0:
      dict_row = {}
      dict_row['mpn'] = str(row['wire_gauge']) + 'mm2' + "-" + "Red"
      dict_row['description'] = DESCRIPTION
      dict_row['manufacturer'] = MANUFACTURER
      total_length = row['length'] * wire_counter[row['cable_des'] +"Red"]
      dict_row['quantity'] = total_length/1000
      dict_row['unit'] = UNIT
      wire_data.append(dict_row)

    if wire_counter.get(row['cable_des'] +"Black",0) > 0:
      dict_row = {}
      dict_row['mpn'] = str(row['wire_gauge']) + 'mm2' + "-" + "Black"
      dict_row['description'] = DESCRIPTION
      dict_row['manufacturer'] = MANUFACTURER
      total_length = row['length'] * wire_counter[row['cable_des'] +"Black"]
      dict_row['quantity'] = total_length/1000
      dict_row['unit'] = UNIT
      wire_data.append(dict_row)

    if wire_counter.get(row['cable_des'] +"White",0) > 0:
      dict_row = {}
      dict_row['mpn'] = str(row['wire_gauge']) + 'mm2' + "-" + "White"
      dict_row['description'] = DESCRIPTION
      dict_row['manufacturer'] = MANUFACTURER
      total_length = row['length'] * wire_counter[row['cable_des'] +"White"]
      dict_row['quantity'] = total_length/1000
      dict_row['unit'] = UNIT
      wire_data.append(dict_row)

  #find unique wires
  wire_set = set()
  for row in wire_data:
    wire_set.add(row['mpn'])

  #create dict with wire mpn and quantity
  mpn_quantity = {}
  for wire in wire_set:
    for row in wire_data:
      if row['mpn'] == wire:
        mpn_quantity[wire] = mpn_quantity.get(wire, 0) + row['quantity']


  #for each mpn_quantity, find mpn row in wiredata, add all coloumnns to dict and tehn append bom data
  for mpn in mpn_quantity:
    for row in wire_data:
      if row['mpn'] == mpn:
        dict_row = {}
        dict_row['mpn'] = mpn
        dict_row['description'] =row['description']
        dict_row['manufacturer'] = row['manufacturer']
        dict_row['quantity'] = mpn_quantity[mpn]
        dict_row['unit'] = row['unit']
        bom_data.append(dict_row)
        break

  return bom_data


  #load MiscBomItems.csv into List[dict]
def add_misc_bom_items(bom_data: List[Dict[str, Any]], filename: str, output_path: str) -> List[Dict[str, Any]]:
  import csv
  import os
  misc_data = []
  with open(os.path.join(output_path, f"{filename}.csv"), mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
      misc_data.append(row)
    csv_file.close()
  bom_data.extend(misc_data)
  return bom_data
    

def db_to_labellist(db_filepath: str, cable_des_filter: List[str]):
  #Load from sql, filter out rows by cable_des_filter
  net_table = fetch_table("NetTable", db_filepath)
  cable_table = fetch_table("CableTable", db_filepath)

  if cable_des_filter:
    net_table = [row for row in net_table if row['cable_des'] in cable_des_filter]
    cable_table = [row for row in cable_table if row['cable_des'] in cable_des_filter]
  
 
  cable_set = set()
  for row in net_table:
    cable_set.add(row['cable_des'])
  
  cable_dict = {}
  for cable in cable_set:
    cable_dict[cable] = []
  
  for cable, label_list in cable_dict.items():
    for row in net_table:
      if row['cable_des'] == cable:
        label_1 = row['comp_des_1'] + '-' + row['conn_des_1']
        label_2 = row['comp_des_2'] + '-' + row['conn_des_2']
        if label_1 not in label_list:
          label_list.append(label_1)
        if label_2 not in label_list:
          label_list.append(label_2)

  # add cable dict to label data
  label_data: List[str] = []
  label_data.append("Cable and Connector Labels:")
  for cable, label_list in cable_dict.items():
    label_data.append(cable)
    for label in label_list:
      label_data.append(label)

  return label_data




  #output List[dict] to xslx
def output_to_xlsx(data: List[Any], filename: str, output_path: str) -> None:
  import pandas as pd
  import os
  
  output_file = os.path.join(output_path, f"{filename}.xlsx")
  df = pd.DataFrame(data)
  df.to_excel(output_file, index=False)


def create_bom(db_filepath: str, cable_des_filter: List[str], output_path: str) -> None:
  bom_data = db_to_BOM(db_filepath, cable_des_filter)
  bom_data = add_misc_bom_items(bom_data, "MiscBOM", output_path)
  output_to_xlsx(bom_data, "BOM", output_path)


def create_labellist(db_filepath: str, cable_des_filter: List[str], output_path: str) -> None:
  label_data = db_to_labellist(db_filepath, cable_des_filter)
  output_to_xlsx(label_data, "LabelList", output_path)



