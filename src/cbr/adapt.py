import json
import os
import random
import copy

from pathlib import Path
from itertools import combinations_with_replacement
from lxml.objectify import StringElement, Element, SubElement

from definitions import CASE_LIBRARY as CASE_LIBRARY_PATH
from case_library import CaseLibrary, ConstraintsBuilder

random.seed(10)


def random_choice(elements, n):
    return elements[random.randint(0, n)]


def subsumed(a, b):
    return a in b


def search_ingredient(ingr_text=None, basic_taste=None, alc_type=None):
    if ingr_text:
        return random.choice(CASE_LIBRARY.findall(".//ingredient[.='{}']".format(ingr_text)))
    if basic_taste:
        return random.choice(CASE_LIBRARY.findall(".//ingredient[@basic_taste='{}']".format(basic_taste)))
    if alc_type:
        return random.choice(CASE_LIBRARY.findall(".//ingredient[@alc_type='{}']".format(alc_type)))
    else:
        return


def adapt_alcs_and_tastes(exc_ingrs, recipe, recipes, alc_type="", basic_taste=""):
    for rec in recipes[1:]:
        similar_ingrs = rec.ingredients.findall(
            "ingredient[@basic_taste='{}'][@alc_type='{}']".format(basic_taste, alc_type)
        )
        for si in similar_ingrs:
            if not subsumed(si.text, exc_ingrs):
                include_ingredient(si, recipe, si.attrib["measure"])
                return
    while True:
        similar_ingr = search_ingredient(basic_taste=basic_taste, alc_type=alc_type)
        if not subsumed(similar_ingr.text, exc_ingrs):
            include_ingredient(similar_ingr, recipe)
            return


def include_ingredient(ingr, recipe, measure="some"):
    ingr.attrib["id"] = f"ingr{len(recipe.findall('ingredients/ingredient'))}"
    ingr.attrib["measure"] = measure
    recipe.find("ingredients").append(ingr)
    step = SubElement(recipe.preparation, "step")
    if measure == "some":
        step._setText(f"add {ingr.attrib['id']} to taste")
    else:
        step._setText(f"add {measure} of {ingr.attrib['id']}")
    recipe.preparation.insert(1, step)


def replace_ingredient(ingr1, ingr2):
    if ingr1.text != ingr2.text:
        if subsumed(ingr1.attrib["basic_taste"], ingr2.attrib["basic_taste"]) and subsumed(
            ingr1.attrib["alc_type"], ingr2.attrib["alc_type"]
        ):
            ingr1._setText(ingr2.text)
            return True
    return False


def count_ingr_ids(step):
    return step.text.count("ingr")


def delete_ingredient(ingr, recipe):
    recipe.ingredients.remove(ingr)
    for step in recipe.preparation.iterchildren():
        if subsumed(ingr.attrib["id"], step.text):
            if count_ingr_ids(step) > 1:
                step._setText(step.text.replace(ingr.attrib["id"], "[IGNORE]"))
            else:
                recipe.preparation.remove(step)


def exclude_ingredient(exc_ingr, recipe, inc_ingrs, recipes):
    if not exc_ingr.attrib["alc_type"]:
        for ingr in inc_ingrs:
            if replace_ingredient(exc_ingr, ingr):
                return
        for rec in recipes[1:]:
            for ingr in rec.ingredients.iterchildren():
                if replace_ingredient(exc_ingr, ingr):
                    return
        for _ in range(20):
            similar_ingr = search_ingredient(
                basic_taste=exc_ingr.attrib["basic_taste"],
                alc_type=exc_ingr.attrib["alc_type"]
            )
            if similar_ingr is None:
                delete_ingredient(exc_ingr, recipe)
                return
            if exc_ingr.text != similar_ingr.text:
                exc_ingr._setText(similar_ingr.text)
                return
    delete_ingredient(exc_ingr, recipe)
    return


def update_ingr_list(recipe):
    alc_types = set()
    basic_tastes = set()
    ingredients = set()
    for ing in recipe.ingredients.iterchildren():
        if ing.attrib["alc_type"]:
            alc_types.add(ing.attrib["alc_type"])
        if ing.attrib["basic_taste"]:
            basic_tastes.add(ing.attrib["basic_taste"])
        ingredients.add(ing.text)
    return alc_types, basic_tastes, ingredients


def adapt(query, recipes):
    recipe = copy.deepcopy(recipes[0])
    alc_types, basic_tastes, ingredients = update_ingr_list(recipe)

    for exc_ingr in query["exc_ingredients"]:
        if subsumed(exc_ingr, ingredients):
            exc_ingr = recipe.find("ingredients/ingredient[.='{}']".format(exc_ingr))
            exclude_ingredient(exc_ingr, recipe, query["ingredients"], recipes)

    alc_types, basic_tastes, ingredients = update_ingr_list(recipe)

    for ingr in query["ingredients"]:
        if not subsumed(ingr.text, ingredients):
            measure = search_ingr_measure(ingr.text, recipes[1:])
            if measure:
                include_ingredient(ingr, recipe, measure)
            else:
                include_ingredient(ingr, recipe)

    alc_types, basic_tastes, ingredients = update_ingr_list(recipe)

    for alc_type in query["alc_type"]:
        if not subsumed(alc_type, alc_types):
            adapt_alcs_and_tastes(query["exc_ingredients"], recipe, recipes, alc_type=alc_type)

    for basic_taste in query["basic_taste"]:
        if not subsumed(basic_taste, basic_tastes):
            adapt_alcs_and_tastes(query["exc_ingredients"], recipe, recipes, basic_taste=basic_taste)

    return recipe


def search_ingr_measure(ingr_text, recipes):
    for rec in recipes:
        for ingr in rec.ingredients.iterchildren():
            if ingr.text == ingr_text:
                return ingr.attrib["measure"]
    return None


if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    query = {
        "category": "ordinary drink",
        "glass": "old-fashioned glass",
        "alc_type": ["vermouth"],
        "basic_taste": ["salty"],
        "ingredients": ["orange juice", "rum"],
        "exc_ingredients": ["mint", "gin", "orange"],
    }

    CONSTRAINT = ConstraintsBuilder(include_category=query["category"], include_glass=query["glass"])
    CASE_LIBRARY = CaseLibrary(CASE_LIBRARY_PATH)
    query["ingredients"] = [search_ingredient(ingr) for ingr in query["ingredients"]]
    recipes = random.choices(CASE_LIBRARY.findall(CONSTRAINT), k=5)

    print(f"Ingredients before: {[e.text for e in recipes[0].findall('ingredients/ingredient')]}")
    print(f"Steps before: {[e.text for e in recipes[0].findall('preparation/step')]}")
    output = adapt(query, recipes)
    print(f"Ingredients after: {[e.text for e in output.findall('ingredients/ingredient')]}")
    print(f"Steps after: {[e.text for e in output.findall('preparation/step')]}")

    print("Done")
