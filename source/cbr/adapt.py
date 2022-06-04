import os
import sys
import re
from pathlib import Path

sys.path.append("..")

import random
from itertools import combinations_with_replacement
from xml.etree.ElementTree import Element
from source.utils.helper import read_xml


random.seed(30)


def random_recipe(path):
    root = read_xml(path)
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


def ordered_combinations(ingr):
    split = ingr.split()
    c = list(combinations_with_replacement(range(len(split)), 2))
    substrings = sorted([" ".join(split[start:end + 1]) for start, end in c], key=len, reverse=True)
    return substrings


def replace_ingredient(ingr1, ingr1_id, ingr2, recipe):
    if ingr1.text != ingr2.text:
        if subsumed(ingr1.attrib["basic_taste"], ingr2.attrib["basic_taste"]) \
                and subsumed(ingr1.attrib["alc_type"], ingr2.attrib["alc_type"]):
            ingr1.text = ingr2.text
            for step in recipe.findall("preparation/step"):
                step.text = step.text.replace(ingr1_id, f"{ingr1.attrib['measure']} of {ingr2.text}")
            # substrings = ordered_combinations(ingr1.text)
            # for step in recipe.findall("preparation/step"):
            #     org_step = step
            #     for sub in substrings:
            #         step.text = step.text.replace(sub, ingr2.text)
            #         if step.text != org_step:
            #             break
            return True
    return False


def count_ingr_ids(step):
    return step.text.count("ingr")


def delete_ingredient(ingr, ingr_id, recipe):
    recipe.find("ingredients").remove(recipe.find("ingredients/ingredient[.='{}']".format(ingr.text)))
    for step in recipe.findall("preparation/step"):
        if subsumed(ingr_id, step.text):
            if count_ingr_ids(step) > 1:
                step.text = step.text.replace(ingr_id, "[IGNORE]")
            else:
                recipe.find("preparation").remove(step)


def exclude_ingredient(exc_ingr, inc_ingrs, recipes):
    exc_ingr_id = recipes[0].find("ingredients/ingredient[.='{}']".format(exc_ingr.text)).attrib["id"]
    replaced = False
    for ingr in inc_ingrs:
        if replace_ingredient(exc_ingr, exc_ingr_id, ingr, recipes[0]):
            return
    for recipe in recipes[1:]:
        for ingr in recipe.findall("ingredients/ingredient"):
            if replace_ingredient(exc_ingr, exc_ingr_id, ingr, recipes[0]):
                return
    delete_ingredient(exc_ingr, exc_ingr_id, recipes[0])


def build_ingredient(ingr_text, path_case_library):
    root = read_xml(path_case_library)
    twin = root.find("cocktail/ingredients/ingredient[.='{}']".format(ingr_text))
    attribs = {
                "basic_taste": twin.attrib["basic_taste"],
                "alc_type": twin.attrib["alc_type"]
                }
    ingr = Element("ingredient", attrib=attribs)
    ingr.text = ingr_text
    return ingr


def replace_ids(recipe):
    map = {ingr.attrib["id"]: f"{ingr.attrib['measure']} of {ingr.text}" for ingr in recipe.findall("ingredients/ingredient")}
    for step in recipe.findall("preparation/step"):
        step.text = re.sub('|'.join(re.escape(k) for k in map), lambda x: map[x.group()], step.text)


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

    for exc_ingr in query["exc_ingredients"]:
        if subsumed(exc_ingr, ingredients):
            exc_ingr = recipe.find("ingredients/ingredient[.='{}']".format(exc_ingr))
            exclude_ingredient(exc_ingr, query["ingredients"], recipes)

    if not subsumed(query["category"], recipe.find("category").text):
        adapt_category(query["category"], recipe)

    if not subsumed(query["glass"], recipe.find("glass").text):
        adapt_glass(query["glass"], recipe)

    for alc in query["alc_type"]:
        if not subsumed(alc, alc_types):
            adapt_alc_type(alc, recipe)

    for taste in query["basic_taste"]:
        if not subsumed(taste, basic_tastes):
            adapt_basic_taste(taste, recipe)

    for ingr in query["ingredients"]:
        if not subsumed(ingr, ingredients):
            include_ingredient(ingr, recipe)

    replace_ids(recipe)

    return recipe


if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    xml_file = os.path.join(data_folder, "case_base.xml")
    query = {"category": "ordinary drink",
             "glass": "xxx",
             "alc_type": ["vermouth", "whisky"],
             "basic_taste": ["sweet", "sour"],
             "ingredients": ["orange juice", "rum"],
             "exc_ingredients": ["light rum jamaican", "milk", "tequila"]
             }
    #query["exc_ingredients"] = [build_ingredient(exc_ingr, xml_file) for exc_ingr in query["exc_ingredients"]]
    query["ingredients"] = [build_ingredient(ingr, xml_file) for ingr in query["ingredients"]]
    recipes = [random_recipe(xml_file) for _ in range(5)]

    print(f"Ingredients before: {[e.text for e in recipes[0].findall('ingredients/ingredient')]}")
    print(f"Steps before: {[e.text for e in recipes[0].findall('preparation/step')]}")
    output = adapt(query, recipes)
    print(f"Ingredients after: {[e.text for e in output.findall('ingredients/ingredient')]}")
    print(f"Steps after: {[e.text for e in output.findall('preparation/step')]}")

    print("Done")
