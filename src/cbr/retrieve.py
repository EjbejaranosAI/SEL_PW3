import os
import random
from pathlib import Path

import numpy as np

# From definitions import CASE_LIBRARY as CASE_LIBRARY_PATH
from case_library import CaseLibrary, ConstraintsBuilder

# from definitions import CASE_LIBRARY as CASE_LIBRARY_PATH
from definitions import CASE_LIBRARY_FILE
from entity.cocktail import Cocktail

random.seed(10)


def search_ingredient(ingr_text=None, basic_taste=None, alc_type=None):
    if ingr_text:
        return random.choice(case_library.findall(".//ingredient[.='{}']".format(ingr_text)))
    if basic_taste:
        return random.choice(case_library.findall(".//ingredient[@basic_taste='{}']".format(basic_taste)))
    if alc_type:
        return random.choice(case_library.findall(".//ingredient[@alc_type='{}']".format(alc_type)))
    else:
        return


# Define a structure that stores all the cases of the dataset divided by category


def similarity_cocktal(cl, constraints, cocktail):
    """Similarity between a set of constraints and a particular cocktail.

    Start with similarity 0, then each constraint is evaluated one by one and increase
    The similarity is according to the feature weight

    Args:
        cl: case library
        constraints (dict): dictionary containing a set of constraints
        cocktail (Element): cocktail Element

    Returns:
        float: normalized similarity
    """
    # Start with cumulative similarity equal to 0
    sim = 0

    # Initialization variable  - normalize final cumulated similarity
    cumulative_norm_score = 0

    # Get cocktails ingredients and alc_type
    c_ingredients = [i.text for i in cocktail.findall("ingredients/ingredient")]
    c_ingredients_atype = [i.attrib["alc_type"] for i in cocktail.findall("ingredients/ingredient")]
    c_ingredients_btype = [i.attrib["basic_taste"] for i in cocktail.findall("ingredients/ingredient")]

    # Evaluate each constraint one by one
    for key in constraints:
        if constraints[key]:

            # Ingredient constraint has highest importance
            if key == "ingredients":
                for ingredient in constraints[key]:
                    # Get ingredient alcohol_type, if any
                    ingredient_alc_type = [k for k in cl.alcohol_dict if ingredient in cl.alcohol_dict[k]]
                    if ingredient_alc_type:
                        itype = "alcohol"
                        ingredient_alc_type = ingredient_alc_type[0]
                    # If the ingredient is not alcoholic, get its basic_taste
                    else:
                        itype = "non-alcohol"
                        ingredient_basic_taste = [k for k in cl.basic_dict if ingredient in cl.basic_dict[k]]

                    # Increase similarity - if constraint ingredient is used in cocktail
                    if ingredient in c_ingredients:
                        sim += cl.sim_weights["ingr_match"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

                    # Increase similarity - if constraint ingredient alc_type is used in cocktail
                    elif itype == "alcohol" and ingredient_alc_type in c_ingredients_atype:
                        sim += cl.sim_weights["ingr_alc_type_match"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

                    # Increase similarity if constraint ingredient basic_taste is used in cocktail
                    elif itype == "non-alcohol" and ingredient_basic_taste in c_ingredients_btype:
                        sim += cl.sim_weights["ingr_basic_taste_match"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

            # Increase similarity if alc_type is a match. Alc_type has a lot of importance,
            # but less than the ingredient constraints
            elif key == "alc_type":
                for atype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if atype == i.attrib["alc_type"]]
                    if len(matches) > 0:
                        sim += cl.sim_weights["alc_type_match"]
                        cumulative_norm_score += cl.sim_weights["alc_type_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_norm_score += cl.sim_weights["alc_type_match"]

            # Increase similarity if basic_taste is a match. Basic_taste has a lot of importance,
            # but less than the ingredient constraints
            elif key == "basic_taste":
                for btype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if btype == i.attrib["basic_taste"]]
                    if len(matches) > 0:
                        sim += cl.sim_weights["basic_taste_match"]
                        cumulative_norm_score += cl.sim_weights["basic_taste_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_norm_score += cl.sim_weights["basic_taste_match"]

            # Increase similarity if glasstype is a match. Glasstype is not very relevant for the case
            elif key == "glasstype":
                if cocktail.find(key).text in constraints[key]:
                    sim += cl.sim_weights["glasstype_match"]
                    cumulative_norm_score += cl.sim_weights["glasstype_match"]
                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_norm_score += cl.sim_weights["glasstype_match"]

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
                        exc_ingredient_basic_taste = [k for k in cl.basic_dict if ingredient in cl.basic_dict[k]]

                    # Decrease similarity if ingredient excluded is found in cocktail
                    if ingredient in c_ingredients:
                        sim += cl.sim_weights["exc_ingr_match"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

                    # Decrease similarity if excluded ingredient alc_type is used in cocktail
                    elif itype == "alcohol" and exc_ingredient_alc_type in c_ingredients_atype:
                        sim += cl.sim_weights["exc_ingr_alc_type_match"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

                    # Decrease similarity if excluded ingredient basic_taste is used in cocktail
                    elif itype == "non-alcohol" and exc_ingredient_basic_taste in c_ingredients_btype:
                        sim += cl.sim_weights["exc_ingr_basic_taste_match"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

            # If one of the excluded alcohol_types is found in the cocktail, similarity is reduced
            elif key == "exc_alc_type":
                for atype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if atype == i.attrib["alc_type"]]
                    if len(matches) > 0:
                        sim += cl.sim_weights["exc_alc_type"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

            # If one of the excluded basic_tastes is found in the cocktail, similarity is reduced
            elif key == "exc_basic_taste":
                for atype in constraints[key]:
                    matches = [i for i in cocktail.find("ingredients/ingredient") if atype == i.attrib["basic_taste"]]
                    if len(matches) > 0:
                        sim += cl.sim_weights["exc_basic_taste"]
                        cumulative_norm_score += cl.sim_weights["ingr_match"]
                    # In case the constraint is not fulfilled we add the weight to the normalization score
                    else:
                        cumulative_norm_score += cl.sim_weights["ingr_match"]

    # Normalization of similarity
    if cumulative_norm_score == 0:
        normalized_sim = 1.0
    else:
        normalized_sim = sim / cumulative_norm_score

    return normalized_sim * float(cocktail.find("utility").text)


def retrieve(query, constraints, cl):
    # 1. SEARCHING
    # Filter elements that correspond to the category constraint
    # If category constraints is not empty
    list_recipes = cl.findall(constraints)

    # 2. SELECTION
    # Compute similarity with each of the cocktails of the searching list
    sim_list = [similarity_cocktal(cl, query, c) for c in list_recipes]

    # Max index
    max_indices = np.argwhere(np.array(sim_list) == np.amax(np.array(sim_list))).flatten().tolist()
    if len(max_indices) > 1:
        index_retrieved = random.choice(max_indices)
    else:
        index_retrieved = max_indices[0]

    # Retrieve case with higher similarity
    retrieved_case = list_recipes[index_retrieved]

    return list_recipes, sim_list, index_retrieved, retrieved_case


if __name__ == "__main__":
    data_folder = os.path.join(Path(os.path.dirname(__file__)).parent.parent, "data")
    query = {
        "category": "cocktail",
        "glass": "collins glass",
        "alc_type": ["vodka"],
        "basic_taste": ["bitter"],
        "ingredients": ["strawberries", "vodka"],
        "exc_ingredients": ["mint", "gin", "lemon"],
    }

    CONSTRAINT = ConstraintsBuilder(include_category=query["category"], include_glass=query["glass"])
    case_library = CaseLibrary(CASE_LIBRARY_FILE)
    query["ingredients"] = [search_ingredient(ingr) for ingr in query["ingredients"]]

    recipes, sim_list, index_retrieved, retrieved_case = retrieve(query, CONSTRAINT, case_library)

    i = len(recipes) - 1
    print(f"Similarity List: {i}")
    print(f"Category: {[e.text for e in recipes[i].findall('category')]}")
    print(f"Ingredients: {[e.text for e in recipes[i].findall('ingredients/ingredient')]}")
    print(f"Steps: {[e.text for e in recipes[i].findall('preparation/step')]}")
    #########################
    print(f"Similarity List: {sim_list}")
    #########################
    print(f"Index Max Similarity: {[index_retrieved]}")
    #########################
    print(f"Category-Retrieved Case: {[e.text for e in retrieved_case.findall('category')]}")
    print(f"Ingredients-Retrieved Case: {[e.text for e in retrieved_case.findall('ingredients/ingredient')]}")
    print(f"Steps-Retrieved Case: {[e.text for e in retrieved_case.findall('preparation/step')]}")

    print("Done")
