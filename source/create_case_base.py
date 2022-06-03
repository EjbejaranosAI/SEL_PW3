import os

import pandas as pd
from lxml import etree
from lxml.etree import SubElement
from pandas import DataFrame

from definitions import CASE_BASE, DATA_PATH


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


def create_case_base(data: DataFrame, output_file):
    # Sort the cocktails by category while keeping the ingredients for the same recipe grouped.
    data = data.sort_values(by=["Category", "Cocktail"])
    cocktails = etree.Element("cocktails")
    previous_cocktail = ""
    cocktail_ingredients = None
    ingredient_idx = 0

    for idx, row in data.iterrows():
        name = row["Cocktail"]
        if name == previous_cocktail:
            add_ingredient(ingredient_idx, row, cocktail_ingredients)
            ingredient_idx += 1
        else:
            ingredient_idx = 0
            cocktail = etree.SubElement(cocktails, "cocktail")
            cocktail_name = etree.SubElement(cocktail, "name")
            cocktail_name.text = name
            cocktail_category = etree.SubElement(cocktail, "category")
            cocktail_category.text = row["Category"]
            cocktail_glass = etree.SubElement(cocktail, "glass")
            cocktail_glass.text = row["Glass"]
            cocktail_ingredients = etree.SubElement(cocktail, "ingredients")
            add_ingredient(ingredient_idx, row, cocktail_ingredients)
            ingredient_idx += 1
            add_preparation(cocktail, row)
            utility = etree.SubElement(cocktail, "utility")
            utility.text = str(1.0)
            derivation = etree.SubElement(cocktail, "derivation")
            derivation.text = "Original"
            evaluation = etree.SubElement(cocktail, "evaluation")
            evaluation.text = "Success"
        previous_cocktail = name

    tree = etree.ElementTree(cocktails)
    tree.write(output_file, pretty_print=True, encoding="utf-8")


def add_preparation(cocktail, row):
    cocktail_preparation = etree.SubElement(cocktail, "preparation")
    steps = row["Steps"].split(". ")
    for s in steps:
        if s:
            step = etree.SubElement(cocktail_preparation, "step")
            step.text = s


if __name__ == "__main__":
    df = pd.read_pickle(os.path.join(DATA_PATH, "processed-cocktails-data.pkl"))
    df = df.sort_values("Cocktail")
    create_case_base(df, CASE_BASE)
