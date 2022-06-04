from lxml import etree, objectify

from definitions import CASE_LIBRARY
from source.entity.cocktail import Cocktail, CocktailList


class CaseLibrary:
    def __init__(self):
        self.ET = objectify.parse(CASE_LIBRARY)
        self.case_library = self.ET.getroot()
        self.cocktails = None

    def findall(self, constraints):
        cocktails = self.case_library.xpath(f"./{constraints}//cocktail")
        return cocktails


class ConstraintsBuilder:
    def __init__(self, category_constraint="", glass_constraint=""):
        self.constraints = "./"
        if category_constraint:
            self.category_constraints = [f"@type='{category_constraint}'"]
        else:
            self.category_constraints = []
        if glass_constraint:
            self.glass_constraint = [f"@type='{glass_constraint}'"]
        else:
            self.glass_constraint = []
        self.ingredient_constraints = []

    def or_category(self, category):
        self.category_constraints.append(f"or @type='{category}'")
        return self

    def or_glass(self, glass_type):
        self.glass_constraint.append(f"or @type='{glass_type}'")
        return self

    def and_ingredient(self, ingredient):
        if self.ingredient_constraints:
            self.ingredient_constraints.append(f"and ingredient='{ingredient}'")
        else:
            self.ingredient_constraints = [f"ingredient='{ingredient}'"]

    def build(self):
        cat_constraints = str.join(" ", self.category_constraints)
        glass_constraint = str.join(" ", self.glass_constraint)
        ingredient_constraints = str.join(" ", self.ingredient_constraints)
        return f"category[{cat_constraints}]/glass[{glass_constraint}]/cocktails/cocktail[{ingredient_constraints}]"


if __name__ == "__main__":
    cl = CaseLibrary()
    print(cl.findall("./category[@type='beer']"))
