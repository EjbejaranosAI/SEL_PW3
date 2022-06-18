import re
from dataclasses import dataclass, field
from typing import List
from xml.etree.ElementTree import Element


@dataclass
class Ingredient:
    id: str = ""
    name: str = ""
    measure: str = ""
    quantity: float = 0.0
    unit: str = ""

    def __str__(self):
        return f"{self.measure} {self.name}" if self.measure == "some" else f"{self.measure} of {self.name}"

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
    UaS: int = 0
    UaF: int = 0
    success_count: int = 0
    failure_count: int = 0

    def __str__(self):
        output = f"""{self.name}
Type of drink: {self.category}
Glass: {self.glass}
Ingredients:
"""

        max_per_line = 4
        steps = self.preparation.copy()
        for i, ingredient in enumerate(self.ingredients):
            steps = [re.sub(f"\\b{ingredient.id}\\b", str(ingredient), step) for step in steps]
            if i == 0:
                output += f"        {ingredient}"
            else:
                if i % max_per_line == 0:
                    output += f",\n        {ingredient}"
                else:
                    output += f", {ingredient}"

        output += "\nPreparation:"
        for i, step in enumerate(steps):

            output += f"\n        {i}. {step}"
        output += "\n"
        return output

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
        UaS = element.UaS
        UaF = element.UaF
        self.success_count = element.success_count
        self.failure_count = element.failure_count

        return self
