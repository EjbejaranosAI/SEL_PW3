from dataclasses import dataclass, field
from typing import List

from lxml.objectify import Element


@dataclass
class Ingredient:
    id: str = ""
    name: str = ""
    measure: str = ""
    quantity: float = 0.0
    unit: str = ""

    def from_element(self, element: Element):
        self.id = element.id
        self.name = element.name
        self.measure = element.measure
        self.quantity = float(element.quantity)
        self.unit = element.unit
        return self


@dataclass
class AlcoholicIngredient(Ingredient):
    alc_type: str = ""


@dataclass
class NonAlcoholicIngredient(Ingredient):
    basic_taste: str = ""


@dataclass
class GarnishIngredient(Ingredient):
    garnish_type: str = ""


@dataclass
class Cocktail:
    name: str = ""
    category: str = ""
    glass: str = ""
    ingredients: List[Ingredient] = field(default_factory=list)
    preparation: List[str] = field(default_factory=list)
    utility: float = 0.0
    derivation: str = ""
    evaluation: str = ""

    def from_element(self, element: Element):
        self.name = element.name
        self.category = element.category
        self.glass = element.glass
        self.ingredients = [Ingredient().from_element(ingredient) for ingredient in element.ingredients]
        self.preparation = [step.text for step in element.preparation.step]
        self.utility = float(element.utility)
        self.derivation = element.derivation
        self.evaluation = element.evaluation
        return self

    def similarity(self, other):
        # TODO: define similarity of a cocktail to another.
        pass


@dataclass
class CocktailList:
    __slots__ = ["cocktails"]
    cocktails: List[Cocktail]
