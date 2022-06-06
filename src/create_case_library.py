import os
import re
from itertools import permutations

import pandas as pd
from lxml import etree
from lxml.etree import SubElement
from pandas import DataFrame

from definitions import CASE_BASE, CASE_LIBRARY, DATA_PATH
from source.utils.helper import powerset


def add_ingredient(id, row, ingredients):
    alc_type = row["Alc_type"]
    alc_type = "" if isinstance(alc_type, float) else alc_type
    basic_taste = row["Basic_taste"]
    basic_taste = "" if isinstance(row["Basic_taste"], float) else basic_taste
    measure = row["Measure"]
    measure = "" if isinstance(measure, float) else measure
    value_ml = row["Value_ml"]
    value_gr = row["Value_gr"]
    unit = ""
    garnish_type = ""
    if value_ml > 0:
        quantity = value_ml
        unit = "ml"
    elif value_gr > 0:
        quantity = value_gr
        unit = "gr"
    else:
        quantity = row["Garnish_amount"]
        garnish_type = row["Garnish_type"]

    ingredient = SubElement(
        ingredients,
        "ingredient",
        id=f"ingr{id}",
        alc_type=str(alc_type),
        basic_taste=str(basic_taste),
        measure=str(measure),
        quantity=str(quantity),
        unit=str(unit),
        garnish_type=str(garnish_type),
    )
    ingredient.text = row["Ingredient"]


def add_preparation(cocktail, row, ingredients_list):
    cocktail_preparation = etree.SubElement(cocktail, "preparation")
    preparation = row["Steps"]
    preparation = re.sub(r"&", "and", preparation)
    for ingr_id, measure, ingredient in ingredients_list:
        ingredient_w = ingredient.split()
        pattern = ""
        longest_match = 0
        best_match = None
        seen_permutations = []
        # Search for the longest match for all possible permutations in the ingredient name
        for combination in powerset(ingredient_w):
            if combination in seen_permutations:
                continue
            else:
                for permutation in permutations(combination):
                    seen_permutations.append(permutation)
                    pattern = r"\s?({}\.?\s?(of)?)?\s?{}\b".format(measure, " ".join(permutation))
                    if "coffee" in permutation:
                        pattern += r"(?!\scup)"
                    match = re.search(pattern, preparation, flags=re.IGNORECASE)
                    if match is not None and len(match.group()) > longest_match:
                        longest_match = len(match.group())
                        best_match = match

        # If there is a match replace by the ingredient ID
        if best_match:
            preparation = re.sub(best_match.re, f" {ingr_id}", preparation)

    steps = re.split(r"(?<!(oz|ml|gr))\. |\b\d+\.", preparation)
    for s in steps:
        if s:
            step = etree.SubElement(cocktail_preparation, "step")
            step.text = s.strip(" .")


def create_case_base(data: DataFrame, output_file):
    # Sort the cocktails by category while keeping the ingredients for the same recipe grouped.
    data = data.sort_values(by=["Category", "Cocktail"])
    grouped_data = data.groupby(["Cocktail"])
    cocktails = etree.Element("cocktails")

    for group_name, df_group in grouped_data:
        ingredient_idx = 0
        ingredients_list = []
        # Initialize cocktail element with the first row of the recipe.
        first_row = df_group.iloc[0]
        cocktail = etree.SubElement(cocktails, "cocktail")
        cocktail_name = etree.SubElement(cocktail, "name")
        cocktail_name.text = group_name
        cocktail_category = etree.SubElement(cocktail, "category")
        cocktail_category.text = first_row["Category"]
        cocktail_glass = etree.SubElement(cocktail, "glass")
        cocktail_glass.text = first_row["Glass"]
        cocktail_ingredients = etree.SubElement(cocktail, "ingredients")
        add_ingredient(ingredient_idx, first_row, cocktail_ingredients)
        ingredients_list.append((f"ingr{ingredient_idx}", first_row["Measure"], first_row["Ingredient"]))
        ingredient_idx += 1

        # Add the rest of the ingredients
        for idx, row in df_group.iloc[1:].iterrows():
            add_ingredient(ingredient_idx, row, cocktail_ingredients)
            ingredients_list.append((f"ingr{ingredient_idx}", row["Measure"], row["Ingredient"]))
            ingredient_idx += 1

        add_preparation(cocktail, first_row, ingredients_list)

        # Add default evaluation metrics
        utility = etree.SubElement(cocktail, "utility")
        utility.text = str(1.0)
        derivation = etree.SubElement(cocktail, "derivation")
        derivation.text = "Original"
        evaluation = etree.SubElement(cocktail, "evaluation")
        evaluation.text = "Success"

    tree = etree.ElementTree(cocktails)
    tree.write(output_file, pretty_print=True, encoding="utf-8")


def create_case_library(output_file):
    root = etree.parse(CASE_BASE).getroot()
    categories = {category.text for category in root.findall("cocktail/category")}
    glass_types = {glass.text for glass in root.findall("cocktail/glass")}
    case_library = etree.Element("case_library")
    for cat in categories:
        category = etree.SubElement(case_library, "category", type=cat)
        for g in glass_types:
            cocktail_list = root.xpath("//cocktail[category=$cat and glass=$g]", cat=cat, g=g)
            if cocktail_list:
                glass = etree.SubElement(category, "glass", type=g)
                cocktails = etree.SubElement(glass, "cocktails")
                cocktails.extend(cocktail_list)

    tree = etree.ElementTree(case_library)
    tree.write(output_file, pretty_print=True, encoding="utf-8")


if __name__ == "__main__":
    df = pd.read_pickle(os.path.join(DATA_PATH, "processed-cocktails-data.pkl"))
    df = df.sort_values("Cocktail")
    create_case_base(df, CASE_BASE)
    create_case_library(CASE_LIBRARY)
