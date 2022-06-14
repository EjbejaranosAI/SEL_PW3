import copy
import random
import re
from typing import Tuple

import numpy as np
from lxml.objectify import SubElement

from definitions import CASE_LIBRARY_FILE as CASE_LIBRARY_PATH
from definitions import USER_SCORE_THRESHOLD, USER_THRESHOLD
from entity.cocktail import Cocktail
from entity.query import Query
from src.cbr.case_library import CaseLibrary, ConstraintsBuilder
from src.utils.helper import count_ingr_ids, replace_ingredient

random.seed(10)


class CBR:
    def __init__(self):
        """
        Case-Based Reasoning system

        Attributes
        ----------
        """
        self.USER_THRESHOLD = USER_THRESHOLD
        self.USER_SCORE_THRESHOLD = USER_SCORE_THRESHOLD
        self.EVALUATION_THRESHOLD = 0.6
        self.case_library = CaseLibrary(CASE_LIBRARY_PATH)
        self.query = None
        self.sim_recipes = []
        self.adapted_recipe = None
        self.ingredients = None
        self.basic_tastes = None
        self.alc_types = None
        self.score_percent = 0.0
        self.evaluation_score = 0.0
        self.similarity_score = 0.0
        self.similarity_evaluation_score = 0.0

    def run_query(self, query, new_name) -> Tuple[Cocktail, Cocktail, float]:
        """
        Run the CBR and obtain a new case based on the given query.

        Parameters
        ----------
        query : `entity.query.Query`
            User query with recipe requirements.
        new_name : str
            The name for the adapted recipe.

        Returns
        -------
        retrieved_case: `Cocktail`
            The retrieved case being adapted.
        adapted_case: `Cocktail`
            The adapted case.
        score : float
            Score of the adapted case given by the :class:`CBR`
        """
        self.retrieve(query)
        self.adapt(new_name)
        score = self.evaluate()
        self.learn()
        retrieved_case = Cocktail().from_element(self.retrieved_case)
        adapted_case = Cocktail().from_element(self.adapted_recipe)
        return retrieved_case, adapted_case, score

    def _search_ingredient(self, ingr_text=None, basic_taste=None, alc_type=None):
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
        for ing in self.adapted_recipe.ingredients.iterchildren():
            if ing.attrib["alc_type"]:
                self.alc_types.add(ing.attrib["alc_type"])
            if ing.attrib["basic_taste"]:
                self.basic_tastes.add(ing.attrib["basic_taste"])
            self.ingredients.add(ing.text)

    def delete_ingredient(self, ingr):
        self.adapted_recipe.ingredients.remove(ingr)
        for step in self.adapted_recipe.preparation.iterchildren():
            if ingr.attrib["id"] in step.text:
                if count_ingr_ids(step) > 1:
                    step._setText(step.text.replace(ingr.attrib["id"], "[IGNORE]"))
                else:
                    self.adapted_recipe.preparation.remove(step)

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
                ingr = self._search_ingredient(
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
        ingr.attrib["id"] = f"ingr{len(self.adapted_recipe.ingredients.ingredient[:])}"
        measure = re.sub(r"\sof\b", "", measure)
        ingr.attrib["measure"] = measure
        self.adapted_recipe.ingredients.append(ingr)
        step = SubElement(self.adapted_recipe.preparation, "step")
        if measure == "some":
            step._setText(f"add {ingr.attrib['id']} to taste")
        else:
            step._setText(f"add {ingr.attrib['id']}")
        self.adapted_recipe.preparation.insert(1, step)

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
            ingr = self._search_ingredient(basic_taste=basic_taste, alc_type=alc_type)
            if ingr.text not in self.query.get_exc_ingredients():
                self.include_ingredient(ingr)
                return

    def retrieve(self, query: Query):
        """
        Retrieves the 5 most similar cases for the given query.

        Parameters
        ----------
        query : :class:`entity.query.Query`
            User query with recipe requirements.
        """
        self.query = query
        self.ingredients = None
        self.basic_tastes = None
        self.alc_types = None

        # 1. SEARCHING
        # Filter elements that correspond to the category constraint
        # If category constraints is not empty
        list_recipes = self.case_library.findall(ConstraintsBuilder().from_query(self.query))

        # If we have less than 5 recipes matching the user constraints,
        # we relax them progressively until having at least 5 recipes.
        counter = 0
        soft_query = copy.deepcopy(self.query)
        while len(list_recipes) < 5:
            if counter == 0:
                soft_query.exc_ingredients = []
            elif counter == 1:
                soft_query.ingredients = []
            elif counter == 2:
                soft_query.basic_tastes = []
            elif counter == 3:
                soft_query.alc_types = []
            elif counter == 4:
                soft_query.glass = ""
            else:
                soft_query.category = ""

            aux_recipes = self.case_library.findall(ConstraintsBuilder().from_query(soft_query))
            list_recipes += aux_recipes
            counter += 1

        # 2. SELECTION
        # Compute similarity with each of the cocktails of the searching list
        sim_list = [self._similarity_cocktail(c) for c in list_recipes]

        # Max index
        max_indices = np.argwhere(np.array(sim_list) == np.amax(np.array(sim_list))).flatten().tolist()
        if len(max_indices) > 1:
            index_retrieved = random.choice(max_indices)
        else:
            index_retrieved = max_indices[0]

        # Retrieve case with higher similarity
        self.retrieved_case = list_recipes[index_retrieved]

        list_recipes.remove(self.retrieved_case)
        sim_list.remove(sim_list[index_retrieved])

        sorted_sim = np.flip(np.argsort(sim_list))
        self.sim_recipes = [copy.deepcopy(list_recipes[i]) for i in sorted_sim[:4]]
        self.adapted_recipe = copy.deepcopy(self.retrieved_case)
        self.update_ingr_list()
        self.query.set_ingredients([self._search_ingredient(ingr) for ingr in self.query.get_ingredients()])

    def _similarity_cocktail(self, cocktail):
        """Similarity between a set of constraints and a particular cocktail.

        Start with similarity 0, then each constraint is evaluated one by one and increase
        The similarity is according to the feature weight

        Parameters
        ----------
        cocktail : lxml.objectify.ObjectifiedElement
            cocktail Element

        Returns
        -------
        float:
            normalized similarity
        """
        # Start with cumulative similarity equal to 0
        sim = 0

        # Initialization variable  - normalize final cumulated similarity
        cumulative_norm_score = 0

        # Get cocktails ingredients and alc_type
        c_ingredients = set()
        c_ingredients_atype = set()
        c_ingredients_btype = set()
        for ingredient in cocktail.ingredients.iterchildren():
            c_ingredients.add(ingredient.text)
            c_ingredients_atype.add(ingredient.attrib["alc_type"])
            c_ingredients_btype.add(ingredient.attrib["basic_taste"])

        # Evaluate each constraint one by one
        for ingredient in self.query.ingredients:
            # Get ingredient alcohol_type, if any
            ingredient_alc_type = self.case_library.ingredients_onto["alcoholic"].get(ingredient, None)
            ingredient_basic_taste = self.case_library.ingredients_onto["non-alcoholic"].get(ingredient, None)
            if ingredient in c_ingredients:
                # Increase similarity - if constraint ingredient is used in cocktail
                sim += self.case_library.sim_weights["ingr_match"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            elif ingredient_alc_type is not None and ingredient_alc_type in c_ingredients_atype:
                # Increase similarity - if constraint ingredient alc_type is used in cocktail
                sim += self.case_library.sim_weights["ingr_alc_type_match"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            elif ingredient_basic_taste is not None and ingredient_basic_taste in c_ingredients_btype:
                # Increase similarity if constraint ingredient basic_taste is used in cocktail
                sim += self.case_library.sim_weights["ingr_basic_taste_match"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            else:
                # In case the constraint is not fulfilled we add the weight to the normalization score
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]

        # Increase similarity if alc_type is a match. Alc_type has a lot of importance,
        # but less than the ingredient constraints
        for alc_type in self.query.alc_types:
            if alc_type in c_ingredients_atype:
                sim += self.case_library.sim_weights["alc_type_match"]
                cumulative_norm_score += self.case_library.sim_weights["alc_type_match"]
            # In case the constraint is not fulfilled we add the weight to the normalization score
            else:
                cumulative_norm_score += self.case_library.sim_weights["alc_type_match"]

        # Increase similarity if basic_taste is a match. Basic_taste has a lot of importance,
        # but less than the ingredient constraints
        for basic_taste in self.query.basic_tastes:
            if basic_taste in c_ingredients_btype:
                sim += self.case_library.sim_weights["basic_taste_match"]
                cumulative_norm_score += self.case_library.sim_weights["basic_taste_match"]
            # In case the constraint is not fulfilled we add the weight to the normalization score
            else:
                cumulative_norm_score += self.case_library.sim_weights["basic_taste_match"]

        # Increase similarity if glass type is a match. Glass type is not very relevant for the case
        if cocktail.glass.text == self.query.glass:
            sim += self.case_library.sim_weights["glass_type_match"]
            cumulative_norm_score += self.case_library.sim_weights["glass_type_match"]
        # In case the constraint is not fulfilled we add the weight to the normalization score
        else:
            cumulative_norm_score += self.case_library.sim_weights["glass_type_match"]

        # If one of the excluded elements in the constraint is found in the cocktail, similarity is reduced
        for ingredient in self.query.exc_ingredients:
            # Get ingredient alcohol_type, if any
            exc_ingredient_alc_type = self.case_library.ingredients_onto["alcoholic"].get(ingredient, None)
            exc_ingredient_basic_taste = self.case_library.ingredients_onto["non-alcoholic"].get(ingredient, None)
            if ingredient in c_ingredients:
                # Decrease similarity if ingredient excluded is found in cocktail
                sim += self.case_library.sim_weights["exc_ingr_match"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            elif exc_ingredient_alc_type is not None and exc_ingredient_alc_type in c_ingredients_atype:
                # Decrease similarity if excluded ingredient alc_type is used in cocktail
                sim += self.case_library.sim_weights["exc_ingr_alc_type_match"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            elif exc_ingredient_basic_taste is not None and exc_ingredient_basic_taste in c_ingredients_btype:
                # Decrease similarity if excluded ingredient basic_taste is used in cocktail
                sim += self.case_library.sim_weights["exc_ingr_basic_taste_match"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            else:
                # In case the constraint is not fulfilled we add the weight to the normalization score
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]

        # If one of the excluded alcohol_types is found in the cocktail, similarity is reduced
        for alc_type in self.query.exc_alc_types:
            if alc_type in c_ingredients_atype:
                sim += self.case_library.sim_weights["exc_alc_type"]
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]
            else:
                # In case the constraint is not fulfilled we add the weight to the normalization score
                cumulative_norm_score += self.case_library.sim_weights["ingr_match"]

        # Normalization of similarity
        if cumulative_norm_score == 0:
            normalized_sim = 1.0
        else:
            normalized_sim = sim / cumulative_norm_score

        return normalized_sim * float(cocktail.find("utility").text)

    def adapt(self, new_name):
        """
        Adapts the recipe according the user requirements
        by excluding ingredients and including other ingredients,
        alcohol types and basic tastes.

        Parameters
        ----------
        new_name : str
            The name for the adapted recipe.
        """
        self.adapted_recipe.name = new_name
        for exc_ingr in self.query.get_exc_ingredients():
            if exc_ingr in self.ingredients:
                exc_ingr = self.adapted_recipe.find("ingredients/ingredient[.='{}']".format(exc_ingr))
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

    # Function to calculate the similarity between adapted recipe and original recipe
    

    # Create a function to evaluate the adapted_recipe and the query. 
    # This function should return the score based on the similarity between the adapted_recipe and the query
    def evaluation(self):
        similarity_ing = 0.0
        similarity_alc = 0.0
        similarity_taste = 0.0
        
        """
        Evaluates the adapted recipe and the query.
        Returns the score based on the similarity between the adapted_recipe and the query.
        """
        # Initialize score
        score = 0
        # Get the parameters from the adapted_recipe
        adapted_recipe_ingredients = self.adapted_recipe.find("ingredients")
        adapted_recipe_alc_types = self.adapted_recipe.find("alc_types")
        adapted_recipe_basic_tastes = self.adapted_recipe.find("basic_tastes")
        # Get the parameters from the query
        query_ingredients = self.query.get_ingredients()
        query_alc_types = self.query.get_alc_types()
        query_basic_tastes = self.query.get_basic_tastes()

        # Calculate the score based on the similarity between the adapted_recipe and the query (using the function above)
        for ingredient in adapted_recipe_ingredients:
            if ingredient.text in query_ingredients:
                similarity_ing += self.similarity(ingredient)
                #if the similarity is higher than 0.9 we add the score to the total score
                score += 3.5 if similarity_ing >= 0.85 else 2 if similarity_ing >= 0.65 else 1 if similarity_ing >= 0.35 else 0
        for alc_type in adapted_recipe_alc_types:
            if alc_type in query_alc_types:
                similarity_alc += self.similarity(alc_type)
                #if the similarity is higher than 0.9 we add the score to the total score
                score += 3.5 if similarity_alc >= 0.85 else 2 if similarity_alc >= 0.65 else 1 if similarity_alc >= 0.35 else 0
        for basic_taste in adapted_recipe_basic_tastes: 
            if basic_taste in query_basic_tastes:
                similarity_taste += self.similarity(basic_taste)
                #if the similarity is higher than 0.9 we add the score to the total score
                score += 3 if similarity_taste >= 0.85 else 2 if similarity_taste >= 0.65 else 1 if similarity_taste >= 0.35 else 0
        self.similarity_evaluation_score = score
        return self.similarity_evaluation_score 

    # Create a function to learn the cases adapted to the case_library
    def Learning(self):
        #Ask the user to put as input an score using the get_user_score function
        self.USER_THRESHOLD = self.get_user_score()
        
        if self.similarity_evaluation_score > self.EVALUATION_THRESHOLD and self.USER_THRESHOLD >= self.USER_SCORE_THRESHOLD:
            #If the score is higher than the threshold we add the adapted recipe to the case_library
            self.case_library.add_case(self.adapted_recipe)
            
            #Function to forget the case from the case library that has less success or with the highest similarity
            #self.forget_case()
        else:
            #If the score is lower than the threshold we forget the adapted recipe and adapt a new recipe to the case
            
            self.adapt(self.adapted_recipe.name)
            self.calculate_similarity()
            self.evaluation()
            #THIS LINES CAN BE DELETED OR NOT, DEPPEND THE FLOW OF THE PROGRAM
            self.case_library.add_case(self.adapted_recipe)
            
            
            #self.forget_case()


        
    # Create a function to forget the case from the case library that has less success or with the highest similarity
    def forget_case(self):
        #Get the cases from the case library
        cases = self.case_library.get_cases()
        #Get the cases with the highest success
        highest_success = max(cases, key=lambda x: x.success)
        #Get the cases with the highest similarity
        highest_similarity = max(cases, key=lambda x: x.similarity)
        #If the highest success is less than the highest similarity, we forget the case with the highest success
        if highest_success.success < highest_similarity.success:
            self.case_library.forget_case(highest_success)
        #If the highest success is greater than or equal to the highest similarity, we forget the case with the highest similarity
        else:
            self.case_library.forget_case(highest_similarity)
        

    # function to ask the user for the USER_SCORE_THRESHOLD value in the recipe file and return the result to the main
    # function to be used in the learning process
    def get_user_score(self):
        """
        Asks the user for the USER_SCORE_THRESHOLD value in the recipe file and
        return the result to the main function to be used in the learning process.

            Returns
            -------
            user_threshold : float
                User threshold value.
        """
        user_threshold = input("Please enter the USER_SCORE_THRESHOLD value: ")
        # updated the user_score_threshold in the class with the user input instance variable
        self.USER_SCORE_THRESHOLD = float(user_threshold)
        return self.USER_SCORE_THRESHOLD

    # Function to know how many recipes are available in the case_library
    def get_recipe_count(self):
        """
        Returns the number of recipes in the case_library.
        """
        return self.adapted_recipe.objects.count()

    # Function to give the user requirements to the recipe
    def get_user_requirements(self):
        """
        Asks the user for the user requirements and returns the result to the main function to be used in the learning process.

            Returns
            -------
            user_requirements : User query with recipe requirements.
        """
        user_requirements = input("Please enter the user requirements: ")

        return user_requirements

    # Function to give information about the recipe available in the case_library
    def get_recipe_info(self):
        """
        Returns the information about the recipes in the case_library.
        """
        info = self.adapted_recipe.objects.all()
        for i in info:
            print(i)

        return info

    # Function to return the list of recipes
    def get_recipe_list(self):
        """
        Returns the list of recipes in the case_library.
        """
        list_recipes = self.adapted_recipe.objects.all()
        return list_recipes

    # Function to return the list of ingredients
    def get_ingredient_list(self):
        """
        Returns the list of ingredients in the case_library.
        """
        ingredient_list = self.ingredient.objects.all()
        return ingredient_list

    # Function to return the list of alc_types
    def get_alc_type_list(self):
        """
        Returns the list of alc_types in the case_library.
        """
        alc_type_list = self.alc_type.objects.all()
        return alc_type_list

    # Function to return the list of basic_tastes
    def get_basic_taste_list(self):
        """
        Returns the list of basic_tastes in the case_library.
        """
        basic_taste_list = self.basic_taste.objects.all()
        return basic_taste_list
