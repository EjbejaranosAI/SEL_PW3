from dataclasses import dataclass
from typing import List


@dataclass
class Ingredient:
    __slots__ = ["id", "name", "measure", "quantity", "unit"]
    id: str
    name: str
    measure: str
    quantity: float
    unit: str


@dataclass
class AlcoholicIngredient(Ingredient):
    __slots__ = ["alc_type"]
    alc_type: str


@dataclass
class NonAlcoholicIngredient(Ingredient):
    __slots__ = ["basic_taste"]
    basic_taste: str


@dataclass
class GarnishIngredient(Ingredient):
    __slots__ = ["garnish_type"]
    garnish_type: str


@dataclass
class Cocktail:
    __slots__ = ["name", "category", "glass", "ingredients", "preparation", "utility", "derivation", "evaluation"]
    name: str
    category: str
    glass: str
    ingredients: List[Ingredient]
    preparation: List[str]
    utility: float
    derivation: str
    evaluation: str

    def similarity(self, other):
        # TODO: define similarity of a cocktail to another.
        pass


@dataclass
class CocktailList:
    __slots__ = ["cocktails"]
    cocktails: List[Cocktail]
