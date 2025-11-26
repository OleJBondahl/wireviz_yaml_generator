#Fetches data from sql database

from model_builder import *
import sqlite3

def fetch_data(query: str, db_filepath: str) -> List[Dict[str, Any]]:
  #fetch data from sql database master.db, with a sql query str
    conn = sqlite3.connect(db_filepath)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_image_data():
  pass

def fetch_connector_data(db_fields: List[str], db_filepath: str) -> List[Dict[str, Any]]:
  #builds sql select query str from list of fields
  #NET_TABLE_FIELDS = "comp_des_1", "comp_des_2", "conn_des_1", "conn_des_2", "pin_1", "pin_2" 
  #NET_TABLE_NAME = "NetTable"

  #net_table_query = build_query(NET_TABLE_NAME, NET_TABLE_FIELDS, db_fields)
  #net_table_data = fetch_data(net_table_query, db_filepath)

  DESIGNATOR_TABLE_FIELDS: List[str] = "comp_des", "conn_des", "conn_mpn"
  DESIGNATOR_TABLE_NAME = "DesignatorTable"
  designator_table_query = build_query(DESIGNATOR_TABLE_NAME, DESIGNATOR_TABLE_FIELDS, DESIGNATOR_TABLE_FIELDS)
  designator_table_data = fetch_data(designator_table_query, db_filepath)
  
  CONNECTOR_TABLE_FIELDS: List[str] = "mpn", "pincount", "mate_mpn"
  CONNECTOR_TABLE_NAME = "ConnectorTable"
  connector_table_query = build_query(CONNECTOR_TABLE_NAME, CONNECTOR_TABLE_FIELDS, CONNECTOR_TABLE_FIELDS)
  connector_table_data = fetch_data(connector_table_query, db_filepath)

  connector_data: List[Dict[str, Any]] = designator_table_data + connector_table_data
  return connector_data


def fetch_cable_data(db_fields: List[str], db_filepath: str) -> List[Dict[str, Any]]:
  NET_TABLE_FIELDS: List[str] = "net_name", "comp_des_1", "comp_des_2", "conn_des_1", "conn_des_2", "pin_1", "pin_2"
  NET_TABLE_NAME = "NetTable"

  net_table_query = build_query(NET_TABLE_NAME, NET_TABLE_FIELDS, db_fields)
  net_table_data = fetch_data(net_table_query, db_filepath)

  cable_data: List[Dict[str, Any]] = net_table_data
  return cable_data



def fetch_connection_data(db_fields: List[str], db_filepath: str) -> List[Dict[str, Any]]:
  NET_TABLE_FIELDS: List[str] = "net_name", "comp_des_1", "comp_des_2", "conn_des_1", "conn_des_2", "pin_1", "pin_2"
  NET_TABLE_NAME = "NetTable"

  net_table_query = build_query(NET_TABLE_NAME, NET_TABLE_FIELDS, db_fields)
  net_table_data = fetch_data(net_table_query, db_filepath)

  connection_data: List[Dict[str, Any]] = net_table_data
  return connection_data


def build_query(TABLE_NAME: str, FIELDS: List[str], db_fields: List[str], query_type: str = "SELECT DISTINCT ") -> str:
    FIELDS_SET = set(FIELDS)
    db_fields_set = set(db_fields)
    
    common_fields = FIELDS_SET & db_fields_set 

    query = query_type + " "
    
    for field in common_fields: 
        query += field + ", "
        
   
    if common_fields:
        query = query[:-2] + " FROM " + TABLE_NAME
    else:
        # Hvis ingen felt matcher, returner en feil eller tom streng (best å feile tidlig)
        raise ValueError("Ingen felles felt funnet for å bygge SELECT-spørring.")

    return query

#test function
#if __name__ == "__main__":
#  connector_data = fetch_connector_data(db_fields=["comp_des_2", "conn_des_2", "pin_2", "mpn", "pincount", "mp_des_3"], db_filepath="master.db")
#  print(connector_data)