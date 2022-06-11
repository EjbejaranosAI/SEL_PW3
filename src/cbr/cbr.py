import random
import copy

from lxml.objectify import SubElement

from definitions import CASE_LIBRARY as CASE_LIBRARY_PATH
from case_library import CaseLibrary
from utils.helper import replace_ingredient, count_ingr_ids

random.seed(10)


class CBR:
    def __init__(self, query, recipes):
        """
        Case-Based Reasoning system

        Parameters
        ----------
        query : Query
            User query with recipe requirements

        recipes : list of lxml ObjectifiedElement

        Attributes
        ----------
        """
        self.case_library = CaseLibrary(CASE_LIBRARY_PATH)
        self.query = query
        self.sim_recipes = recipes[1:]
        self.recipe = copy.deepcopy(recipes[0])
        self.ingredients = None
        self.basic_tastes = None
        self.alc_types = None
        self.update_ingr_list()
        self.query.set_ingredients([self.search_ingredient(ingr) for ingr in self.query.get_ingredients()])

    def search_ingredient(self, ingr_text=None, basic_taste=None, alc_type=None):
        if ingr_text:
            return random.choice(self.case_library.findall(".//ingredient[.='{}']".format(ingr_text)))
        if basic_taste:
            return random.choice(self.case_library.findall(".//ingredient[@basic_taste='{}']".format(basic_taste)))
        if alc_type:
            return random.choice(self.case_library.findall(".//ingredient[@alc_type='{}']".format(alc_type)))
        else:
            return

    def update_ingr_list(self):
        self.alc_types = set()
        self.basic_tastes = set()
        self.ingredients = set()
        for ing in self.recipe.ingredients.iterchildren():
            if ing.attrib["alc_type"]:
                self.alc_types.add(ing.attrib["alc_type"])
            if ing.attrib["basic_taste"]:
                self.basic_tastes.add(ing.attrib["basic_taste"])
            self.ingredients.add(ing.text)

    def delete_ingredient(self, ingr):
        self.recipe.ingredients.remove(ingr)
        for step in self.recipe.preparation.iterchildren():
            if ingr.attrib["id"] in step.text:
                if count_ingr_ids(step) > 1:
                    step._setText(step.text.replace(ingr.attrib["id"], "[IGNORE]"))
                else:
                    self.recipe.preparation.remove(step)

    def search_ingr_measure(self, ingr_text):
        for recipe in self.sim_recipes:
            for ingr in recipe.ingredients.iterchildren():
                if ingr.text == ingr_text:
                    return ingr.attrib["measure"]
        return None

    def exclude_ingredient(self, exc_ingr):
        """

        Parameters
        ----------
        exc_ingr

        Returns
        -------

        """
        if not exc_ingr.attrib["alc_type"]:
            for ingr in self.query.get_ingredients():
                if replace_ingredient(exc_ingr, ingr):
                    return
            for recipe in self.sim_recipes:
                for ingr in recipe.ingredients.iterchildren():
                    if replace_ingredient(exc_ingr, ingr):
                        return
            for _ in range(20):
                ingr = self.search_ingredient(
                    basic_taste=exc_ingr.attrib["basic_taste"],
                    alc_type=exc_ingr.attrib["alc_type"]
                )
                if ingr is None:
                    self.delete_ingredient(exc_ingr)
                    return
                if exc_ingr.text != ingr.text:
                    exc_ingr._setText(ingr.text)
                    return
        self.delete_ingredient(exc_ingr)
        return

    def include_ingredient(self, ingr, measure="some"):
        ingr.attrib["id"] = f"ingr{len(self.recipe.ingredients.ingredient[:])}"
        ingr.attrib["measure"] = measure
        self.recipe.ingredients.append(ingr)
        step = SubElement(self.recipe.preparation, "step")
        if measure == "some":
            step._setText(f"add {ingr.attrib['id']} to taste")
        else:
            step._setText(f"add {measure} of {ingr.attrib['id']}")
        self.recipe.preparation.insert(1, step)

    def adapt_alcs_and_tastes(self, alc_type="", basic_taste=""):
        for recipe in self.sim_recipes:
            ingrs = recipe.ingredients.findall(
                "ingredient[@basic_taste='{}'][@alc_type='{}']".format(basic_taste, alc_type)
            )
            for ingr in ingrs:
                if ingr.text not in self.query.get_exc_ingredients():
                    self.include_ingredient(ingr, ingr.attrib["measure"])
                    return
        while True:
            ingr = self.search_ingredient(basic_taste=basic_taste, alc_type=alc_type)
            if ingr.text not in self.query.get_exc_ingredients():
                self.include_ingredient(ingr)
                return

    def adapt(self):
        for exc_ingr in self.query.get_exc_ingredients():
            if exc_ingr in self.ingredients:
                exc_ingr = self.recipe.find("ingredients/ingredient[.='{}']".format(exc_ingr))
                self.exclude_ingredient(exc_ingr)

        self.update_ingr_list()

        for ingr in self.query.get_ingredients():
            if ingr.text not in self.ingredients:
                measure = self.search_ingr_measure(ingr.text)
                if measure:
                    self.include_ingredient(ingr, measure)
                else:
                    self.include_ingredient(ingr)

        self.update_ingr_list()

        for alc_type in self.query.get_alc_types():
            if alc_type not in self.alc_types:
                self.adapt_alcs_and_tastes(alc_type=alc_type)

        for basic_taste in self.query.get_basic_tastes():
            if basic_taste not in self.basic_tastes:
                self.adapt_alcs_and_tastes(basic_taste=basic_taste)
