from dataclasses import dataclass


@dataclass
class Query:
    def __init__(self):
        self.category = None
        self.glass = None
        self.ingredients = None
        self.exc_ingredients = None
        self.alc_types = None
        self.basic_tastes = None

    def set_category(self, category: str):
        self.category = category

    def set_glass(self, glass: str):
        self.glass = glass

    def set_ingredients(self, ingredients: list[str]):
        self.ingredients = ingredients

    def set_exc_ingredients(self, exc_ingredients: list[str]):
        self.exc_ingredients = exc_ingredients

    def set_alc_types(self, alc_types: list[str]):
        self.alc_types = alc_types

    def set_basic_taste(self, basic_taste: list[str]):
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

    def get_basic_taste(self):
        return self.basic_tastes
