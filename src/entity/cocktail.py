from dataclasses import dataclass, field
from typing import List
from xml.etree.ElementTree import Element

from _distutils_hack import override
from lxml import etree, objectify


@dataclass
class Ingredient:
    id: str = ""
    name: str = ""
    measure: str = ""
    quantity: float = 0.0
    unit: str = ""

    def from_element(self, element: Element):
        self.id = element.attrib["id"]
        self.name = element.text
        self.measure = element.attrib["measure"]
        self.quantity = float(element.attrib["quantity"])
        self.unit = element.attrib["unit"]
        return self


@dataclass
class AlcoholicIngredient(Ingredient):
    alc_type: str = ""

    def from_element(self, element):
        super(AlcoholicIngredient, self).from_element(element)
        self.alc_type = element.attrib["alc_type"]
        return self


@dataclass
class NonAlcoholicIngredient(Ingredient):
    basic_taste: str = ""

    def from_element(self, element):
        super(NonAlcoholicIngredient, self).from_element(element)
        self.basic_taste = element.attrib["basic_taste"]
        return self


@dataclass
class GarnishIngredient(Ingredient):
    garnish_type: str = ""

    def from_element(self, element):
        super(GarnishIngredient, self).from_element(element)
        self.garnish_type = element.attrib["garnish_type"]
        return self


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
        for ingr in element.ingredients.iterchildren():
            if ingr.attrib["alc_type"]:
                self.ingredients.append(AlcoholicIngredient().from_element(ingr))
            elif ingr.attrib["basic_taste"]:
                self.ingredients.append(NonAlcoholicIngredient().from_element(ingr))
            else:
                self.ingredients.append(GarnishIngredient().from_element(ingr))
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
