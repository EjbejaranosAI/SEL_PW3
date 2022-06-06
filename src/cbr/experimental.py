from definitions import CASE_LIBRARY
from src.cbr.case_library import CaseLibrary

if __name__ == "__main__":
    cl = CaseLibrary(CASE_LIBRARY)
    print(cl.drink_types)
    print(cl.glass_types)
    print(cl.alc_types)
    print(cl.taste_types)
    print(cl.garnish_types)
    print(cl.ingredients)
