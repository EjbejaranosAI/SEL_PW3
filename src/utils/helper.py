import os
import re
import xml.etree.ElementTree as ET
from itertools import chain, combinations
from typing import Union

import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(1, len(s) + 1))


# Function to get the path of the current file
def get_path():
    path = os.path.dirname(os.path.abspath(__file__))
    return path


# Function to descompress a zip from a path to a file
def descompress_zip(path, file):
    import zipfile

    zip_ref = zipfile.ZipFile(path, "r")
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


def bar_plot(df: DataFrame, column: Union[int, str]):
    if isinstance(column, str):
        series = df[column]
    else:
        series = df.iloc[:, column]
    series.value_counts().plot.bar()
    plt.show()


def replace_ids(recipe):
    equiv = {
        ingr.attrib["id"]: f"{ingr.attrib['measure']} of {ingr.text}"
        for ingr in recipe.findall("ingredients/ingredient")
    }
    for step in recipe.findall("preparation/step"):
        step.text = re.sub("|".join(re.escape(k) for k in equiv), lambda x: equiv[x.group()], step.text)


def count_ingr_ids(step):
    return step.text.count("ingr")


def replace_ingredient(ingr1, ingr2):
    if ingr1.text != ingr2.text:
        if (
            ingr1.attrib["basic_taste"] == ingr2.attrib["basic_taste"]
            and ingr1.attrib["alc_type"] == ingr2.attrib["alc_type"]
        ):
            ingr1._setText(ingr2.text)
            return True
    return False
