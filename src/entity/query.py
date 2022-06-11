from dataclasses import dataclass


@dataclass
class Query:
    def __init__(self):
        """
        Wrapper class for user queries.

        Attributes
        ----------
        category : str
            Category of the recipe.

        glass : str
            Glass to serve the recipe in.

        ingredients : list[str]
            Ingredients to include in the recipe.

        exc_ingredients : list[str]
            Ingredient to exclude from the recipe.

        alc_types : list[str]
            Alcohol types to include in the recipe.

        basic_tastes : list[str]
            Basic tastes to include in the recipe.
        """
        self.category = None
        self.glass = None
        self.ingredients = None
        self.exc_ingredients = None
        self.alc_types = None
        self.basic_tastes = None

    def set_category(self, category):
        self.category = category

    def set_glass(self, glass: str):
        self.glass = glass

    def set_ingredients(self, ingredients):
        self.ingredients = ingredients

    def set_exc_ingredients(self, exc_ingredients):
        self.exc_ingredients = exc_ingredients

    def set_alc_types(self, alc_types):
        self.alc_types = alc_types

    def set_basic_tastes(self, basic_taste):
        self.basic_tastes = basic_taste

    def get_category(self):
        return self.category

    def get_glass(self):
        return self.glass

    def get_ingredients(self):
        return self.ingredients

    def get_exc_ingredients(self):
        return self.exc_ingredients

    def get_alc_types(self):
        return self.alc_types

    def get_basic_tastes(self):
        return self.basic_tastes
