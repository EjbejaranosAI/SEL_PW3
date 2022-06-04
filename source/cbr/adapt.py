import os
import sys
from pathlib import Path

sys.path.append("..")

import random
from itertools import combinations_with_replacement
from xml.etree.ElementTree import Element
from source.utils.helper import read_xml


random.seed(31)


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


def ordered_combinations(ingr):
    split = ingr.split()
    c = list(combinations_with_replacement(range(len(split)), 2))
    substrings = sorted([" ".join(split[start:end + 1]) for start, end in c], key=len, reverse=True)
    return substrings


def replace_ingredient(ingr1, ingr2, recipe):
    if ingr1.text != ingr2.text:
        if subsumed(ingr1.attrib["basic_taste"], ingr2.attrib["basic_taste"]) \
                and subsumed(ingr1.attrib["alc_type"], ingr2.attrib["alc_type"]):
            recipe.find("ingredients/ingredient[.='{}']".format(ingr1.text)).text = ingr2.text
            substrings = ordered_combinations(ingr1.text)
            for step in recipe.findall("preparation/step"):
                org_step = step
                for sub in substrings:
                    step.text = step.text.replace(sub, ingr2.text)
                    if step.text != org_step:
                        break
            return True
    return False


# def replace_ingredient(ingr1, ingr2, recipe, path_case_library):
#     if not isinstance(ingr1, Element):
#         ingr1 = build_ingredient(ingr1, path_case_library)
#     if not isinstance(ingr2, Element):
#         ingr2 = build_ingredient(ingr2, path_case_library)
#     return replace_ingredient_(ingr1, ingr2, recipe)


def count_ingr_ids(step):
    # TODO
    return -1


def delete_ingredient(ingr, recipe):
    recipe.find("ingredients").remove(recipe.find("ingredients/ingredient[.='{}']".format(ingr.text)))
    for step in recipe.findall("preparation/step"):
        if subsumed(ingr.text, step.text):
            if count_ingr_ids(step) > 1:
                # TODO
                pass
            else:
                recipe.find("preparation").remove(step)


def exclude_ingredient(exc_ingr, inc_ingrs, recipes):
    replaced = False
    for ingr in inc_ingrs:
        if replace_ingredient(exc_ingr, ingr, recipes[0]):
            return
    for recipe in recipes:
        for ingr in recipe.findall("ingredients/ingredient"):
            if replace_ingredient(exc_ingr, ingr, recipes[0]):
                return
    delete_ingredient(exc_ingr, recipes[0])


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
        if subsumed(exc_ingr.text, ingredients):
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

    return recipe


if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    xml_file = os.path.join(data_folder, "case_base.xml")
    query = {"category": "ordinary drink",
             "glass": "xxx",
             "alc_type": ["vermouth", "whisky"],
             "basic_taste": ["sweet", "sour"],
             "ingredients": ["orange juice", "rum"],
             "exc_ingredients": ["blackcurrant cordial", "cider"]
             }
    query["exc_ingredients"] = [build_ingredient(exc_ingr, xml_file) for exc_ingr in query["exc_ingredients"]]
    query["ingredients"] = [build_ingredient(ingr, xml_file) for ingr in query["ingredients"]]
    recipes = [random_recipe(xml_file) for _ in range(5)]

    print(f"Ingredients before: {[e.text for e in recipes[0].findall('ingredients/ingredient')]}")
    print(f"Steps before: {[e.text for e in recipes[0].findall('preparation/step')]}")
    output = adapt(query, recipes)
    print(f"Ingredients after: {[e.text for e in output.findall('ingredients/ingredient')]}")
    print(f"Steps after: {[e.text for e in output.findall('preparation/step')]}")

    print("Done")
