#fetches data from choosen database, creates instances, calls yaml builder on instances
from sql_data_loader import *
from yaml_builder import *
from model_builder import *
from typing import List
from sql_mapping import *


def db_to_yaml(db_fields: List[str], db_filepath: str, yaml_filepath: str, csv: bool = False) -> None:
  if csv:
    print("not implemented yet")

  
  raw_connector_data = fetch_connector_data(db_fields, db_filepath)
  mapped_connector_data = map_connector_data(raw_connector_data)
  connectors = create_connectors(mapped_connector_data)

  raw_cables = fetch_cable_data(db_fields, db_filepath)
  mapped_cable_data = map_cable_data(raw_cables)
  cables = create_cables(mapped_cable_data)

  raw_connections = fetch_connection_data(db_fields, db_filepath)
  mapped_connection_data = map_connection_data(raw_connections)
  connections = create_connections(mapped_connection_data)

  #raw_images = fetch_image_data()
  #images = create_images(raw_images)

  instances = {
    'connectors': connectors,
    'cables': cables,
    'connections': connections,
    #'images': images
  }

  build_yaml(instances=instances, yaml_filepath=yaml_filepath)


#test function
if __name__ == "__main__":
  db_fields = [
    "comp_des_1", 
    "comp_des_2", 
    "conn_des_1", 
    "conn_des_2", 
    "pin_1", 
    "pin_2",
    "net_name",
    "mpn", 
    "pincount", 
    "mate_mpn",
    "mp_des_3",
    ]

  db_to_yaml(db_fields=db_fields, db_filepath="master.db", yaml_filepath="test.yaml")






  