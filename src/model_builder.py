from typing import Dict, Any
from dataclasses import dataclass, field
from typing import List, Optional, Union
from model import *
from sql_mapping import *


#loads data from standard python datatypes into dataclasses and holds their instances
# data must come in dictionary with necesarry fields:

def create_images(data: List[Dict[str, Any]]) -> List[Image]:
  """
  Creates a list of Image dataclass instances from a list of dictionaries.
  """
  image_instances = []
  for image_data in data:
    image_instances.append(Image(**image_data))
  return image_instances

def create_connectors(data: List[Dict[str, Any]]) -> List[Connector]:
  """
  Creates a list of Connector dataclass instances from a list of dictionaries.
  """
  connector_instances = []
  
  for row in data:
    connector_instances.append(Connector(**row))

  return connector_instances

def create_cables(data: List[Dict[str, Any]]) -> List[Cable]:
  """
  Creates a list of Cable dataclass instances from a list of dictionaries.
  """
  cable_instances = []

  for row in data:
    cable_instances.append(Cable(**row))
  return cable_instances


def create_connections(data: List[Dict[str, Any]]) -> List[Connection]:
  """
  Creates a list of Connection dataclass instances from a list of dictionaries.
  """
  connection_instances = []
  for connection_data in data:
    connection_instances.append(Connection(**connection_data))
  return connection_instances