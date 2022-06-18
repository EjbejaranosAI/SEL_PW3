import logging
import os
import random
import re
import sys
from pathlib import Path

sys.path.append(os.fspath(Path(__file__).resolve().parent.parent.parent))

from definitions import LOG_FILE
from src.cbr.cbr import CBR
from src.entity.query import Query

query = Query()
cbr = CBR()


def all_inputs_exist(elements, possible_values):
    for element in elements:
        if element in possible_values:
            continue
        else:
            print(f'-- Error. "{element}" is not in the library. Another value must be specified.')
            return False
    return True


def score_is_valid(score):
    try:
        score = float(score)
        if 0 <= score <= 10:
            return True
        else:
            print("-- Error. The score must be between 0 and 10.")
            return False
    except ValueError:
        print("-- Error. The score must be a float.")
        return False


print("- Welcome to CBR Cocktails.")
print('- Please, enter the name of the recipe and your preferences. Write "suggest" to see examples.\n')

messages = [
    "- Type of drink (e.g.: beer, ordinary drink): ",
    "- Type of glass (e.g.: old-fashioned glass, pint glass): ",
    "- Type of alcohol (e.g.: gin, triple sec): ",
    "- Taste of the drink (e.g.: sour, salty): ",
    "- Ingredients (e.g: cherry, rum): ",
    "- Ingredients to exclude (e.g: banana, vodka): ",
]

actions = [
    query.set_category,
    query.set_glass,
    query.set_alc_types,
    query.set_basic_tastes,
    query.set_ingredients,
    query.set_exc_ingredients,
]

suggestion_pools = [
    list(map(str, cbr.case_library.drink_types)),
    list(map(str, cbr.case_library.glass_types)),
    list(map(str, cbr.case_library.alc_types)),
    list(map(str, cbr.case_library.taste_types)),
    list(map(str, cbr.case_library.ingredients)),
    list(map(str, cbr.case_library.ingredients)),
]

logging.basicConfig(
    filename=LOG_FILE,
    format="%(asctime)s [%(name)s] - %(levelname)s: %(message)s",
    filemode="w",
    level=logging.INFO,
)

while True:
    recipe_name = input("- Name of the recipe: ")
    if recipe_name:
        break
    else:
        print("-- Error. A name must be specified.")
for message, action, suggestion_pool in zip(messages, actions, suggestion_pools):
    print("")
    while True:
        # Takes input and removes extra spaces, empty elements and repeated elements
        x = list(set(filter(None, re.sub(" +", " ", input(message)).split(", "))))
        if (action == query.set_category or action == query.set_glass) and len(x) != 1:
            if len(x) < 1:
                print("-- Error. A value must be specified.")
            if len(x) > 1:
                print("-- Error. This field accepts only one value.")
        elif not x:
            break
        elif x == ["suggest"]:
            print(f"-- Suggestions: {', '.join(random.sample(suggestion_pool, min(5, len(suggestion_pool))))}")

        else:
            if all_inputs_exist(x, suggestion_pool):
                action(x)
                break

retrieved_case, adapted_case = cbr.run_query(query, recipe_name)
print("\n- Here is the recipe:")
print(adapted_case)

while True:
    score = input("- Evaluate this recipe with a score from 1 to 10 (e.g.: 7.5): ")
    if score_is_valid(score):
        score = float(score)
        cbr.evaluation(score)
        break

print("\n- Evaluation sent.")
print("- Done.")
