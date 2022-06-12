import copy
import random

from lxml.objectify import SubElement

from definitions import CASE_LIBRARY_FILE as CASE_LIBRARY_PATH
from src.cbr.case_library import CaseLibrary
from src.utils.helper import count_ingr_ids, replace_ingredient

random.seed(10)


class CBR:
    USER_THRESHOLD = 0.85
    USER_SCORE_THRESHOLD = 0.85
    def __init__(self):
        """
        Case-Based Reasoning system

        Attributes
        ----------
        """
        self.case_library = CaseLibrary(CASE_LIBRARY_PATH)
        self.query = None
        self.sim_recipes = []
        self.recipe = None
        self.ingredients = None
        self.basic_tastes = None
        self.alc_types = None

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
        When the ingredient is not alcohol, replaces it in the recipe by an
        ingredient with the same basic_taste in the list of ingredients
        to include or in the list of similar recipes.
        If such an ingredient is not found or the ingredient to exclude is
        an alcohol, deletes it from the recipe ingredients and preparation.

        Parameters
        ----------
        exc_ingr: :class:`lxml.objectify.ObjectifiedElement`
            Ingredient to exclude.
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
                    basic_taste=exc_ingr.attrib["basic_taste"], alc_type=exc_ingr.attrib["alc_type"]
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
        """
        Includes an ingredient in the recipe.

        Parameters
        ----------
        ingr : :class:`lxml.objectify.ObjectifiedElement`
            Ingredient to include in the recipe.
        measure : str
            Quantity of the ingredient to include.
        """
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
        """
        Finds an ingredient with a certain alcohol type or basic taste
        in the list of similar recipes or de case library and includes it
        in the recipe.

        Parameters
        ----------
        alc_type : str
            Type of alcohol to include.
        basic_taste
            Type of basic taste to include.
        """
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

    def retrieve(self, query, recipes):
        """

        Parameters
        ----------
        query : :class: `entity.query.Query` or None
            User query with recipe requirements.

        recipes : list of :class:`lxml.objectify.ObjectifiedElement` or None
            List of recipes similar to the query.

        Returns
        -------

        """
        self.query = query
        self.sim_recipes = recipes[1:]
        self.recipe = copy.deepcopy(recipes[0])
        self.ingredients = None
        self.basic_tastes = None
        self.alc_types = None
        self.update_ingr_list()
        self.query.set_ingredients([self.search_ingredient(ingr) for ingr in self.query.get_ingredients()])

    def adapt(self):
        """
        Adapts the recipe according the user requirements
        by excluding ingredients and including other ingredients,
        alcohol types and basic tastes.
        """
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
    
    # EVALUATION
    def evaluate(self, query):
        """
        Evaluates the recipe according to the user requirements and the adapted_solution.

        Parameters
        ----------
        query :  User query with recipe requirements and adapted_solution.

        Returns
        -------
        score : float with the evaluation between the user requirements and the adapted_solution requirements.
        
        """
        score = 0
        for ingr in self.query.get_ingredients():
            if ingr.text in self.adapted_solution.get_ingredients():
                score += 1
        for alc_type in self.query.get_alc_types():
            if alc_type in self.adapted_solution.get_alc_types():
                score += 1
        for basic_taste in self.query.get_basic_tastes():
            if basic_taste in self.adapted_solution.get_basic_tastes():
                score += 1
        
        self.score_percent = (score / len(self.query.get_ingredients())) * 100
        self.evaluation_score = score / (len(query.get_ingredients()) + len(query.get_alc_types()) + len(query.get_basic_tastes()))
        
        # Evaluate the similarity between the retrieved recipe and the adapted_solution
        self.similarity_score = self.similarity(self.adapted_solution)
        self.similarity_evaluation_score = self.evaluation_score * self.similarity_score

        return self.evaluation_score * self.similarity_evaluation_score

    # Learning the adapted recipe in the case_library if the score_percent is lower than the EVALUATION_THRESHOLD and the USER_THRESHOLD is equal or higher than the USER_SCORE_THRESHOLD
    def learn(self, query):
        """
        Learns the recipe according to the user requirements and the adapted_solution.

        Parameters
        ----------
        query :  User query with recipe requirements and adapted_solution.

        Returns
        -------
        score : float with the evaluation between the user requirements 
        and the adapted_solution requirements.
        
        """
        if self.score_percent < self.EVALUATION_THRESHOLD and self.USER_THRESHOLD >= self.USER_SCORE_THRESHOLD:
            self.adapted_solution.save()
            return True
        #else: get another recipe from the case_library and adapt it again until the score_percent is lower than the EVALUATION_THRESHOLD 
        else:   
            self.adapted_solution = self.get_random_recipe()
            self.adapt()
            self.adapted_solution.save()
            #EVALUATE THE RECIPE AGAIN
            self.evaluate(query)
            print("Adapted solution: {}".format(self.adapted_solution.get_recipe_name()))
            #learn the score again the retrieved recipe and the adapted solution again until the USER_THRESHOLD is equal or higher than the USER_SCORE_THRESHOLD
            self.learn(query)
            return False
            

