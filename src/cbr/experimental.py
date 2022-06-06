from copy import deepcopy

from lxml import etree

from definitions import CASE_LIBRARY
from src.cbr.case_library import CaseLibrary

if __name__ == "__main__":
    cl = CaseLibrary(CASE_LIBRARY)
    c = cl.findall(".//cocktail")
    a = c[0]
    print(type(a))
    b = deepcopy(a)
    # print(b.get("id"))
    # etree.dump(a.getparent())
    cl.add_case(b)
    # etree.dump(b.getparent())
    # etree.dump(a)
    # etree.dump(b)
    # etree.dump(cl.case_library)
    print(cl.drink_types)
    print(cl.glass_types)
    print(cl.alc_types)
    print(cl.taste_types)
    print(cl.garnish_types)
    print(cl.ingredients)