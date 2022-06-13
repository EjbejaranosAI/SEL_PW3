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


def similarity_cocktail(cl, constraints, cocktail):
    """Similarity between a set of constraints and a particular cocktail.

    Start with similarity 0, then each constraint is evaluated one by one and increase
    The similarity is according to the feature weight

    Parameters
    ----------
    cl : CaseLibrary
    constraints : dict
        Dictionary containing a set of constraints.
    cocktail : lxml.objectify.ObjectifiedElement
        cocktail Element

    Returns
    -------
    float:
        normalized similarity
    """
    # Start with cumulative similarity equal to 0
    sim = 0

    # Initialization variable  - normalize final cumulated similarity
    cumulative_norm_score = 0

    # Get cocktails ingredients and alc_type
    c_ingredients = set()
    c_ingredients_atype = set()
    c_ingredients_btype = set()
    for ingredient in cocktail.ingredients.iterchildren():
        c_ingredients.add(ingredient.text)
        c_ingredients_atype.add(ingredient.attrib["alc_type"])
        c_ingredients_btype.add(ingredient.attrib["basic_taste"])

    # Evaluate each constraint one by one
    for key in constraints:
        if key == "ingredients":
            for ingredient in constraints[key]:
                # Get ingredient alcohol_type, if any
                ingredient_alc_type = None
                ingredient_basic_taste = None
                for alcohol, ingredients in cl.alcohol_dict.items():
                    if ingredient in ingredients:
                        ingredient_alc_type = alcohol
                        break
                # If the ingredient is not alcoholic, get its basic_taste
                if ingredient_alc_type is None:
                    for taste, ingredients in cl.taste_dict.items():
                        if ingredient in ingredients:
                            ingredient_basic_taste = taste
                            break

                # Increase similarity - if constraint ingredient is used in cocktail
                if ingredient in c_ingredients:
                    sim += cl.sim_weights["ingr_match"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

                # Increase similarity - if constraint ingredient alc_type is used in cocktail
                elif ingredient_alc_type is not None and ingredient_alc_type in c_ingredients_atype:
                    sim += cl.sim_weights["ingr_alc_type_match"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

                # Increase similarity if constraint ingredient basic_taste is used in cocktail
                elif ingredient_basic_taste is not None and ingredient_basic_taste in c_ingredients_btype:
                    sim += cl.sim_weights["ingr_basic_taste_match"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

        # Increase similarity if alc_type is a match. Alc_type has a lot of importance,
        # but less than the ingredient constraints
        elif key == "alc_type":
            for btype in constraints[key]:
                if btype in c_ingredients_atype:
                    sim += cl.sim_weights["alc_type_match"]
                    cumulative_norm_score += cl.sim_weights["alc_type_match"]
                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_norm_score += cl.sim_weights["alc_type_match"]

        # Increase similarity if basic_taste is a match. Basic_taste has a lot of importance,
        # but less than the ingredient constraints
        elif key == "basic_taste":
            for btype in constraints[key]:
                if btype in c_ingredients_btype:
                    sim += cl.sim_weights["basic_taste_match"]
                    cumulative_norm_score += cl.sim_weights["basic_taste_match"]
                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_norm_score += cl.sim_weights["basic_taste_match"]

        # Increase similarity if glasstype is a match. Glasstype is not very relevant for the case
        elif key == "glass":
            if cocktail.glass.text in constraints[key]:
                sim += cl.sim_weights["glass_type_match"]
                cumulative_norm_score += cl.sim_weights["glass_type_match"]
            # In case the constraint is not fulfilled we add the weight to the normalization score
            else:
                cumulative_norm_score += cl.sim_weights["glass_type_match"]

        # If one of the excluded elements in the constraint is found in the cocktail, similarity is reduced
        elif key == "exc_ingredients":
            for ingredient in constraints[key]:
                # Get excluded_ingredient alcohol_type, if any
                exc_ingredient_alc_type = None
                exc_ingredient_basic_taste = None
                for alcohol, ingredients in cl.alcohol_dict.items():
                    if ingredient in ingredients:
                        exc_ingredient_alc_type = alcohol
                        break
                # If the ingredient is not alcoholic, get its basic_taste
                if exc_ingredient_alc_type is None:
                    for taste, ingredients in cl.taste_dict.items():
                        if ingredient in ingredients:
                            exc_ingredient_basic_taste = taste
                            break

                # Decrease similarity if ingredient excluded is found in cocktail
                if ingredient in c_ingredients:
                    sim += cl.sim_weights["exc_ingr_match"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

                # Decrease similarity if excluded ingredient alc_type is used in cocktail
                elif exc_ingredient_alc_type is not None and exc_ingredient_alc_type in c_ingredients_atype:
                    sim += cl.sim_weights["exc_ingr_alc_type_match"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

                # Decrease similarity if excluded ingredient basic_taste is used in cocktail
                elif exc_ingredient_basic_taste is not None and exc_ingredient_basic_taste in c_ingredients_btype:
                    sim += cl.sim_weights["exc_ingr_basic_taste_match"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

        # If one of the excluded alcohol_types is found in the cocktail, similarity is reduced
        elif key == "exc_alc_type":
            for btype in constraints[key]:
                if btype in c_ingredients_atype:
                    sim += cl.sim_weights["exc_alc_type"]
                    cumulative_norm_score += cl.sim_weights["ingr_match"]
                # In case the constraint is not fulfilled we add the weight to the normalization score
                else:
                    cumulative_norm_score += cl.sim_weights["ingr_match"]

        # If one of the excluded basic_tastes is found in the cocktail, similarity is reduced
        elif key == "exc_basic_taste":
            for btype in constraints[key]:
                if btype in c_ingredients_atype:
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
    sim_list = [similarity_cocktail(cl, query, c) for c in list_recipes]

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
