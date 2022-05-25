import xml.etree.ElementTree as ET
import os
import pandas as pd
from ast import literal_eval
# Function to get the path of the current file  
def get_path():
    path = os.path.dirname(os.path.abspath(__file__))
    return path
# Function to descompress a zip from a path to a file
def descompress_zip(path, file):
    import zipfile
    zip_ref = zipfile.ZipFile(path, 'r')
    zip_ref.extractall(file)
    zip_ref.close()

    
# Function to read xml file from a path and return the root element
def read_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root


def count_ingredients(data: pd.Series):
    """
    :param data: DataFrame column of ingredients
    :return: number and list of ingredients
    """
    ingredients = []
    series = data.apply(lambda x: x.strip("[]").replace("'", "").split(", "))
    for s in series:
        ingredients = ingredients + s.unique().tolist()
    return len(ingredients), ingredients
