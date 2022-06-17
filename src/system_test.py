import random
import time

import os
import sys
from pathlib import Path

sys.path.append(os.fspath(Path(__file__).resolve().parent.parent))
sys.path.append(os.fspath(Path(__file__).resolve().parent.parent.parent))

from entity.query import Query
from cbr.case_library import CaseLibrary
from cbr.cbr import CBR
from definitions import CASE_LIBRARY_FILE, ROOT_PATH

output_path = os.path.join(ROOT_PATH, "system_tests")
os.makedirs(output_path, exist_ok=True)

N_QUERIES = 100
MAX_N_VALUES = 5

case_library = CaseLibrary(CASE_LIBRARY_FILE)
query = Query()
cbr = CBR()

actions = [
            query.set_category,
            query.set_glass,
            query.set_ingredients,
            query.set_exc_ingredients,
            query.set_basic_tastes,
            query.set_alc_types
            ]

pools = [
                case_library.drink_types,
                case_library.glass_types,
                case_library.ingredients,
                case_library.ingredients,
                case_library.taste_types,
                case_library.alc_types
                ]


def build_query():
    for action, pool in zip(actions, pools):
        if action == query.set_category or action == query.set_glass:
            action(random.choice(pool))
        else:
            action(random.sample(pool, random.randint(0, MAX_N_VALUES)))


test = f"test{random.randint(0, 10000)}.txt"
total_time = 0
for _ in range(N_QUERIES):
    build_query()
    name = f"MyRecipe{random.randint(0, 10000)}"
    start = time.time()
    retrieved_case, adapted_case = cbr.run_query(query, name)
    cbr.evaluation(0)
    total_time += time.time() - start

    with open(os.path.join(output_path, test), "a") as f:
        f.write("--------------\n")
        f.write(f"Query:\n{str(query)}")
        f.write(f"\n\nRetrieved case:\n{retrieved_case}")
        f.write(f"\nAdapted case:\n{adapted_case}")
        f.write("--------------\n\n")


with open(os.path.join(output_path, test), "a") as f:
    f.write(f"\n\nTotal number of queries: {N_QUERIES}")
    f.write(f"\nTotal time: {total_time}")

