import os
from pathlib import Path
import sys
sys.path.append('..')

import random
from utils.helper import read_xml


def random_recipe(path):
    root = read_xml(path)
    #xml_recipe = root[random.randint(0, len(root)-1)]
    # recipe = {}
    # for att in xml_recipe:
    #     recipe[att.tag] = att.text
    return root[random.randint(0, len(root)-1)]


def adapt_glass(glass, recipe):
    recipe.find("glass").text = glass


def subsumed(a, b):
    return a in b


def adapt(query, recipe):
    if not subsumed(query["glass"], recipe.find("glass").text):
        adapt_glass(query["glass"], recipe)


if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    xml_file = os.path.join(data_folder, "case_base.xml")
    query = {"category": "ordinary drink",
             "glass": "xxx",
             "alc_type": ["vermouth", "whisky"],
             "basic_taste": ["sweet", "sour"],
             "ingredients": ["whisky", "cherry liqueur"],
             "exclude_ingredients": ["dry vermouth", "lemon peel"]
             }
    recipe = random_recipe(xml_file)
    adapt(query, recipe)
