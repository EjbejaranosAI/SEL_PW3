import os
import random
import shutil
import sys
import time
from pathlib import Path

sys.path.append(os.fspath(Path(__file__).resolve().parent.parent))
sys.path.append(os.fspath(Path(__file__).resolve().parent.parent.parent))

from cbr.cbr import CBR
from definitions import CASE_LIBRARY_FILE, ROOT_PATH
from entity.query import Query

output_path = os.path.join(ROOT_PATH, "system_tests")
os.makedirs(output_path, exist_ok=True)

N_QUERIES = 300
MAX_N_VALUES = 5
random.seed(2022)

tmp_case_library = "tmp_case_library.xml"
shutil.copyfile(CASE_LIBRARY_FILE, tmp_case_library)

cbr = CBR(tmp_case_library)
query = Query()

actions = [
    query.set_category,
    query.set_glass,
    query.set_ingredients,
    query.set_exc_ingredients,
    query.set_basic_tastes,
    query.set_alc_types,
]

pools = [
    cbr.case_library.drink_types,
    cbr.case_library.glass_types,
    cbr.case_library.ingredients,
    cbr.case_library.ingredients,
    cbr.case_library.taste_types,
    cbr.case_library.alc_types,
]


def fix_ingr_lists():
    """
    Ensures that none of ingredients to exclude in the query
    are in the ingredients to include list.
    """
    match = map(lambda i: i in query.get_exc_ingredients(), query.get_ingredients())
    if any(match):
        idxs = [i for i, val in enumerate(match) if val]
        exc_ingredients = query.get_exc_ingredients()
        fail_idxs = []
        for i in idxs:
            j = 0
            while True:
                exc_ingredients[i] = random.choice(cbr.case_library.ingredients)
                if exc_ingredients[i] not in query.get_ingredients():
                    break
                if j > 10:
                    fail_idxs.append(i)
                    break
        for i in fail_idxs:
            del exc_ingredients[i]
        query.set_exc_ingredients(exc_ingredients)
    else:
        return


def build_query():
    for action, pool in zip(actions, pools):
        if action == query.set_category or action == query.set_glass:
            action(random.choice(pool))
        else:
            action(random.sample(pool, random.randint(0, MAX_N_VALUES)))
    fix_ingr_lists()


test = f"test{time.strftime('%d-%H%M%S')}.txt"
total_time = 0
for i in range(N_QUERIES):
    print(i)
    build_query()
    name = f"MyRecipe{random.randint(0, 10000)}"
    start = time.time()
    retrieved_case, adapted_case = cbr.run_query(query, name)
    cbr.evaluate(random.random() * 10)
    total_time += time.time() - start

    with open(os.path.join(output_path, test), "a", encoding="utf-8") as f:
        f.write("--------------\n")
        f.write(f"Query:\n{query}")
        f.write(f"\n\nRetrieved case:\n{retrieved_case}")
        f.write(f"\nAdapted case:\n{adapted_case}")
        f.write("--------------\n\n")


with open(os.path.join(output_path, test), "a", encoding="utf-8") as f:
    f.write(f"\n\nTotal number of queries: {N_QUERIES}")
    f.write(f"\nTotal time: {total_time}")

os.remove(tmp_case_library)
