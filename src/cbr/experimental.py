from copy import deepcopy

from lxml import etree

from definitions import CASE_LIBRARY
from src.cbr.case_library import CaseLibrary, ConstraintsBuilder

if __name__ == "__main__":
    cl = CaseLibrary(CASE_LIBRARY)
    c = cl.findall(".//cocktail")
    a = c[0]
    print(type(a))
    b = deepcopy(a)
    cl.add_case(b)
    ingredients = cl.findall(ConstraintsBuilder().filter_ingredient(["banana", "cherry"]))
    etree.dump(ingredients[0])
    print(cl.drink_types)
    print(cl.glass_types)
    print(cl.alc_types)
    print(cl.taste_types)
    print(cl.garnish_types)
    print(cl.ingredients)
