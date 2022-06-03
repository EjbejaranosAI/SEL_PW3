import os
from pathlib import Path
import sys

sys.path.append('..')

import random
from xml.etree.ElementTree import SubElement
from utils.helper import read_xml


def random_recipe(path):
    root = read_xml(path)
    # xml_recipe = root[random.randint(0, len(root)-1)]
    # recipe = {}
    # for att in xml_recipe:
    #     recipe[att.tag] = att.text
    return root[random.randint(0, len(root) - 1)]


def adapt_glass(glass, recipe):
    recipe.find("glass").text = glass


def adapt_category(category, recipe):
    # TODO: adapt category if there is time
    return recipe


def subsumed(a, b):
    return a in b


def adapt_alc_type(alc, recipe):
    pass


def adapt_basic_taste(taste, recipe):
    pass


def include_ingredient(ing, recipe):
    pass


def replace_ingredient(ingr1, ingr2, recipe):
    if subsumed(ingr1.attrib["basic_taste"], ingr2.attrib["basic_taste"]) \
            and subsumed(ingr1.attrib["alc_type"], ingr2.attrib["alc_type"]):
        recipe.find("ingredients/ingredient[.=ingr1.text]").text = ingr2.text
        return True
    return False


def exclude_ingredient(exc_ingr, inc_ingrs, recipes):
    replaced = False
    for ingr in inc_ingrs:
        replaced = replace_ingredient(exc_ingr, ingr, recipes[0])
        if replaced:
            return
    for recipe in recipes:
        for ingr in recipe.findall("ingredients/ingredient"):
            replaced = replace_ingredient(exc_ingr, ingr, recipes[0])
            if replaced:
                return
    recipes[0].findall("ingredients/ingredient").remove(recipes[0].find("ingredients/ingredient[.=exc_ingr.text]"))


def adapt(query, recipes):
    recipe = recipes[0]
    alc_types = set()
    basic_tastes = set()
    ingredients = set()
    for ing in recipe.find("ingredients"):
        if ing.attrib["alc_type"]:
            alc_types.add(ing.attrib["alc_type"])
        if ing.attrib["basic_taste"]:
            basic_tastes.add(ing.attrib["basic_taste"])
        ingredients.add(ing.text)

    exc_ingrs = query["exclude_ingredients"]

    for exc_ingr in exc_ingrs:
        if subsumed(exc_ingr, ingredients):
            exclude_ingredient(exc_ingr, recipe)

    if not subsumed(query["category"], recipe.find("category").text):
        adapt_category(query["category"], recipe)

    if not subsumed(query["glass"], recipe.find("glass").text):
        adapt_glass(query["glass"], recipe)

    for alc in query["alc_type"]:
        if not subsumed(alc, alc_types):
            adapt_alc_type(alc, recipe)

    for taste in query["basic_tastes"]:
        if not subsumed(taste, basic_tastes):
            adapt_basic_taste(taste, recipe)

    for ingr in query["ingredients"]:
        if not subsumed(ingr, ingredients):
            include_ingredient(ingr, recipe)

    return recipe[0]


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
    recipes = [random_recipe(xml_file) for _ in range(5)]
    adapt(query, recipes)
