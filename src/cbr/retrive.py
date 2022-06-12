import json
import os
import random
import copy

from pathlib import Path
from itertools import combinations_with_replacement
from lxml.objectify import StringElement, Element, SubElement

#from definitions import CASE_LIBRARY as CASE_LIBRARY_PATH
from case_library import CaseLibrary, ConstraintsBuilder

import itertools

CASE_LIBRARY_PATH = "C:/Users/greci/Documents/Maestria/FIB/UPC - SEL/Proyecto/Proyecto3/SEL_PW3-Grupo_Grecia/data/case_library.xml"

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
                include_ingredient(si, recipe)
                return
    while True:
        similar_ingr = search_ingredient(basic_taste=basic_taste, alc_type=alc_type)
        if not subsumed(similar_ingr.text, exc_ingrs):
            include_ingredient(similar_ingr, recipe)
            return


def include_ingredient(ingr, recipe):
    ingr.attrib["id"] = f"ingr{len(recipe.findall('ingredients/ingredient'))}"
    ingr.attrib["measure"] = "some"
    recipe.find("ingredients").append(ingr)
    step = SubElement(recipe.preparation, "step")
    step._setText(f"add {ingr.attrib['id']} to taste")
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
        for _ in recipes[1:]:
            for ingr in recipe.ingredients.iterchildren():
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

# Define a structure that stores all the cases of the dataset divided by category

def compute_similarity(cl, constraints, cocktail):
    """ Compute the similarity between a set of constraints and a particular cocktail.

    Start with similarity 0. Then, evaluate each constraint one by one and increase
    similarity according to the feature weight.

    Args:
        constraints (dict): dictionary containing a set of constraints
        cocktail (Element): cocktail Element

    Returns:
        float: normalized similarity
    """
    # Start with cumulative similarity equal to 0
    sim = 0

    # Initialize variable to normalize the final cumulated similarity
    cumulative_normalization_score = 0

    # Get cocktails ingredients and alc_type
    c_ingredients = [i.text for i in cocktail.findall('ingredients/ingredient')]
    c_ingredients_atype = [i.attrib['alc_type'] for i in cocktail.findall('ingredients/ingredient')]
    c_ingredients_btype = [i.attrib['basic_taste'] for i in cocktail.findall('ingredients/ingredient')]

    # Evaluate each constraint one by one
    for key in constraints:
        if constraints[key]:

            # Ingredient constraint has highest importance
            if key == "ingredients/ingredient":
                for ingredient in constraints[key]:
                    # Get ingredient alcohol_type, if any
                    ingredient_alc_type = [k for k in cl.alcohol_dict if ingredient in cl.alcohol_dict[k]]
                    if ingredient_alc_type:
                        itype = "alcohol"
                        ingredient_alc_type = ingredient_alc_type[0]
                    # If the ingredient is not alcoholic, get its basic_taste
                    else:
                        itype = "non-alcohol"
                        ingredient_basic_taste = [k for k in cl.basic_dict if ingredient in cl.basic_dict[k]][0]

                    # Increase similarity if constraint ingredient is used in cocktail
                    if ingredient in c_ingredients:
                        sim += cl.similarity_weights["ingr_match"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

                    # Increase similarity if constraint ingredient alc_type is used in cocktail
                    elif itype == "alcohol" and ingredient_alc_type in c_ingredients_atype:
                        sim += cl.similarity_weights["ingr_alc_type_match"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

                    # Increase similarity if constraint ingredient basic_taste is used in cocktail
                    elif itype == "non-alcohol" and ingredient_basic_taste in c_ingredients_btype:
                        sim += cl.similarity_weights["ingr_basic_taste_match"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

            # Increase similarity if alc_type is a match. Alc_type has a lot of importance,
            # but less than the ingredient constraints
            elif key == "alc_type":
                for atype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if atype == i.attrib['alc_type']]
                    if len(matches) > 0:
                        sim += cl.similarity_weights["alc_type_match"]
                        cumulative_normalization_score += cl.similarity_weights["alc_type_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_normalization_score += cl.similarity_weights["alc_type_match"]

            # Increase similarity if basic_taste is a match. Basic_taste has a lot of importance,
            # but less than the ingredient constraints
            elif key == "basic_taste":
                for btype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if btype == i.attrib['basic_taste']]
                    if len(matches) > 0:
                        sim += cl.similarity_weights["basic_taste_match"]
                        cumulative_normalization_score += cl.similarity_weights["basic_taste_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_normalization_score += cl.similarity_weights["basic_taste_match"]

            # Increase similarity if glasstype is a match. Glasstype is not very relevant for the case
            elif key == "glasstype":
                if cocktail.find(key).text in constraints[key]:
                    sim += cl.similarity_weights["glasstype_match"]
                    cumulative_normalization_score += cl.similarity_weights["glasstype_match"]
                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_normalization_score += cl.similarity_weights["glasstype_match"]

            # If one of the excluded elements in the constraint is found in the cocktail, similarity is reduced
            elif key == "exc_ingredients":
                for ingredient in constraints[key]:
                    # Get excluded_ingredient alcohol_type, if any
                    exc_ingredient_alc_type = [k for k in cl.alcohol_dict if ingredient in cl.alcohol_dict[k]]
                    if exc_ingredient_alc_type:
                        itype = "alcohol"
                        exc_ingredient_alc_type = exc_ingredient_alc_type[0]
                        
                    # If the excluded_ingredient is not alcoholic, get its basic_taste
                    else:
                        itype = "non-alcohol"
                        exc_ingredient_basic_taste = \
                            [k for k in cl.basic_dict if ingredient in cl.basic_dict[k]][0]

                    # Decrease similarity if ingredient excluded is found in cocktail
                    if ingredient in c_ingredients:
                        sim += cl.similarity_weights["exc_ingr_match"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

                    # Decrease similarity if excluded ingredient alc_type is used in cocktail
                    elif itype == "alcohol" and exc_ingredient_alc_type in c_ingredients_atype:
                        sim += cl.similarity_weights["exc_ingr_alc_type_match"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

                    # Decrease similarity if excluded ingredient basic_taste is used in cocktail
                    elif itype == "non-alcohol" and exc_ingredient_basic_taste in c_ingredients_btype:
                        sim += cl.similarity_weights["exc_ingr_basic_taste_match"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

            # If one of the excluded alcohol_types is found in the cocktail, similarity is reduced
            elif key == "exc_alc_type":
                for atype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if atype == i.attrib['alc_type']]
                    if len(matches) > 0:
                        sim += cl.similarity_weights["exc_alc_type"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

            # If one of the excluded basic_tastes is found in the cocktail, similarity is reduced
            elif key == "exc_basic_taste":
                for atype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if atype == i.attrib['basic_taste']]
                    if len(matches) > 0:
                        sim += cl.similarity_weights["exc_basic_taste"]
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_normalization_score += cl.similarity_weights["ingr_match"]

    # Normalize the obtained similarity
    if cumulative_normalization_score == 0:
        normalized_sim = 1.0
    else:
        normalized_sim = sim / cumulative_normalization_score

    return normalized_sim * float(cocktail.find("utility").text)

def retrieval(query, constraints, cl):

    # SEARCHING PHASE
    # Filter elements that correspond to the category constraint
    # If category constraints is not empty
    searching_list = cl.findall(constraints)

    # SELECTION PHASE
    # Compute similarity with each of the cocktails of the searching list    
    sim_list = [compute_similarity(cl, query,c) for c in searching_list]
    
    return searching_list, sim_list

if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    query = {
        "category": "coffee / tea",
        "glass": "irish coffee cup",
        "alc_type": ["whisky"],
        "basic_taste": ["salty"],
        "ingredients": ["orange juice", "rum"],
        "exc_ingredients": ["mint", "gin", "orange"],
    }

    CONSTRAINT = ConstraintsBuilder(include_category=query["category"], include_glass=query["glass"])
    CASE_LIBRARY = CaseLibrary(CASE_LIBRARY_PATH)
    query["ingredients"] = [search_ingredient(ingr) for ingr in query["ingredients"]]
    
    output,simlist = retrieval(query, CONSTRAINT,CASE_LIBRARY)
    print(f"Category: {[e.text for e in output[2].findall('category')]}")
    print(f"Ingredients: {[e.text for e in output[2].findall('ingredients/ingredient')]}")
    print(f"Steps: {[e.text for e in output[2].findall('preparation/step')]}")
    print(simlist)

    print("Done")
