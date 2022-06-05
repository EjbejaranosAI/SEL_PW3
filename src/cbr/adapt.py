import os
import sys
import random
from pathlib import Path

sys.path.append("..")

import random
from itertools import combinations_with_replacement
from xml.etree.ElementTree import Element, SubElement
from src.utils.helper import read_xml
from definitions import CASE_BASE

random.seed(10)


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


def adapt_alcs_and_tastes(exc_ingrs, recipes, alc_type="", basic_taste=""):
    for recipe in recipes[1:]:
        similar_ingrs = recipe.findall("ingredients/ingredient[@basic_taste='{}'][@alc_type='{}']".format(basic_taste, alc_type))
        for si in similar_ingrs:
            if not subsumed(si.text, exc_ingrs):
                include_ingredient(si, recipes[0])
                return
    while True:
        similar_ingr = search_ingredient(CASE_BASE, basic_taste=basic_taste, alc_type=alc_type)
        if not subsumed(similar_ingr.text, exc_ingrs):
            include_ingredient(similar_ingr, recipes[0])
            return


def include_ingredient(ingr, recipe):
    ingr.attrib["id"] = f"ingr{len(recipe.findall('ingredients/ingredient'))}"
    ingr.attrib["measure"] = "some"
    recipe.find("ingredients").append(ingr)
    step = Element("step")
    step.text = f"add {ingr.attrib['id']} to taste"
    recipe.find("preparation").insert(0, step)


# def ordered_combinations(ingr):
#     split = ingr.split()
#     c = list(combinations_with_replacement(range(len(split)), 2))
#     substrings = sorted([" ".join(split[start:end + 1]) for start, end in c], key=len, reverse=True)
#     return substrings


def replace_ingredient(ingr1, ingr1_id, ingr2, recipe):
    if ingr1.text != ingr2.text:
        if subsumed(ingr1.attrib["basic_taste"], ingr2.attrib["basic_taste"]) \
                and subsumed(ingr1.attrib["alc_type"], ingr2.attrib["alc_type"]):
            ingr1.text = ingr2.text
            # for step in recipe.findall("preparation/step"):
            #     step.text = step.text.replace(ingr1_id, f"{ingr1.attrib['measure']} of {ingr2.text}")
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
    for ingr in inc_ingrs:
        if replace_ingredient(exc_ingr, exc_ingr_id, ingr, recipes[0]):
            return
    for recipe in recipes[1:]:
        for ingr in recipe.findall("ingredients/ingredient"):
            if replace_ingredient(exc_ingr, exc_ingr_id, ingr, recipes[0]):
                return
    while True:
        similar_ingr = search_ingredient(CASE_BASE, basic_taste=exc_ingr.attrib["basic_taste"], alc_type=exc_ingr.attrib["alc_type"])
        if similar_ingr is None:
            delete_ingredient(exc_ingr, exc_ingr_id, recipes[0])
            return
        if exc_ingr.text != similar_ingr.text:
            exc_ingr.text = similar_ingr.text
            return


def search_ingredient(path_case_library, ingr_text=None, basic_taste=None, alc_type=None):
    root = read_xml(path_case_library)
    if ingr_text:
        return random.choice(root.findall("cocktail/ingredients/ingredient[.='{}']".format(ingr_text)))
    if basic_taste:
        return random.choice(root.findall("cocktail/ingredients/ingredient[@basic_taste='{}']".format(basic_taste)))
    if alc_type:
        return random.choice(root.findall("cocktail/ingredients/ingredient[@alc_type='{}']".format(alc_type)))
    else:
        return


def update_ingr_list(recipe):
    alc_types = set()
    basic_tastes = set()
    ingredients = set()
    for ing in recipe.find("ingredients"):
        if ing.attrib["alc_type"]:
            alc_types.add(ing.attrib["alc_type"])
        if ing.attrib["basic_taste"]:
            basic_tastes.add(ing.attrib["basic_taste"])
        ingredients.add(ing.text)
    return alc_types, basic_tastes, ingredients


def adapt(query, recipes):
    recipe = recipes[0]
    alc_types, basic_tastes, ingredients = update_ingr_list(recipe)

    if not subsumed(query["category"], recipe.find("category").text):
        adapt_category(query["category"], recipe)

    if not subsumed(query["glass"], recipe.find("glass").text):
        adapt_glass(query["glass"], recipe)

    for exc_ingr in query["exc_ingredients"]:
        if subsumed(exc_ingr, ingredients):
            exc_ingr = recipe.find("ingredients/ingredient[.='{}']".format(exc_ingr))
            exclude_ingredient(exc_ingr, query["ingredients"], recipes)

    alc_types, basic_tastes, ingredients = update_ingr_list(recipe)

    for ingr in query["ingredients"]:
        if not subsumed(ingr.text, ingredients):
            include_ingredient(ingr, recipe)

    alc_types, basic_tastes, ingredients = update_ingr_list(recipe)

    for alc_type in query["alc_type"]:
        if not subsumed(alc_type, alc_types):
            adapt_alcs_and_tastes(query["exc_ingredients"], recipes, alc_type=alc_type)

    for basic_taste in query["basic_taste"]:
        if not subsumed(basic_taste, basic_tastes):
            adapt_alcs_and_tastes(query["exc_ingredients"], recipes, basic_taste=basic_taste)

    return recipe


if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    query = {"category": "ordinary drink",
             "glass": "xxx",
             "alc_type": ["vermouth", "whisky"],
             "basic_taste": ["sweet", "sour", "salty"],
             "ingredients": ["orange juice", "rum"],
             "exc_ingredients": ["lemon juice", "gin", "orange"]
             }
    query["ingredients"] = [search_ingredient(CASE_BASE, ingr_text=ingr) for ingr in query["ingredients"]]
    recipes = [random_recipe(CASE_BASE) for _ in range(5)]

    print(f"Ingredients before: {[e.text for e in recipes[0].findall('ingredients/ingredient')]}")
    print(f"Steps before: {[e.text for e in recipes[0].findall('preparation/step')]}")
    output = adapt(query, recipes)
    print(f"Ingredients after: {[e.text for e in output.findall('ingredients/ingredient')]}")
    print(f"Steps after: {[e.text for e in output.findall('preparation/step')]}")

    print("Done")
