from lxml import objectify

from definitions import CASE_LIBRARY


class CaseLibrary:
    def __init__(self):
        self.ET = objectify.parse(CASE_LIBRARY)
        self.case_library = self.ET.getroot()
        self.cocktails = None

    def findall(self, constraints):
        if isinstance(constraints, str):
            return self.case_library.xpath(constraints)
        elif isinstance(constraints, ConstraintsBuilder):
            return self.case_library.xpath(constraints.build())
        else:
            raise TypeError("constraints must be string or ConstraintsBuilder.")


class ConstraintsBuilder:
    def __init__(self, category_constraint="", glass_constraint=""):
        self.constraints = "./"
        if category_constraint:
            self.category_constraints = [f"@type='{category_constraint}'"]
        else:
            self.category_constraints = []
        if glass_constraint:
            self.glass_constraint = [f"@type='{glass_constraint}'"]
        else:
            self.glass_constraint = []
        self.ingredient_constraints = dict()

    def or_category(self, category):
        self.category_constraints.append(f"or @type='{category}'")
        return self

    def or_glass(self, glass_type):
        self.glass_constraint.append(f"or @type='{glass_type}'")
        return self

    # def and_alc_type(self, alc_type):
    #     alc_constraints = self.ingredient_constraints.get('alc_type', [])
    #     if alc_constraints:
    #         alc_constraints.append((f"and @acl_type='{alc_type}'"))
    #     else:
    #         alc_constraints.append([f"@alc_type='{alc_type}'"])
    #     return self

    def or_alc_type(self, alc_type):
        alc_constraints = self.ingredient_constraints.get('alc_type', [])
        if alc_constraints:
            alc_constraints.append(f"or @acl_type='{alc_type}'")
        else:
            self.ingredient_constraints['alc_type'] = [f"@alc_type='{alc_type}'"]
        return self

    # def and_basic_taste(self, basic_taste):
    #     taste_constraints = self.ingredient_constraints.get('basic_taste', [])
    #     if taste_constraints:
    #         taste_constraints.append(f"and @basic_taste='{basic_taste}'")
    #     else:
    #         taste_constraints.append([f"@basic_taste='{basic_taste}'"])
    #     return self

    def or_basic_taste(self, basic_taste):
        taste_constraints = self.ingredient_constraints.get('basic_taste', [])
        if taste_constraints:
            taste_constraints.append(f"or @basic_taste='{basic_taste}'")
        else:
            self.ingredient_constraints['basic_taste'] = [f"@basic_taste='{basic_taste}'"]
        return self

    def or_garnish_type(self, garnish_type):
        garnish_constraints = self.ingredient_constraints.get('garnish_type', [])
        if garnish_constraints:
            garnish_constraints.append(f"or @garnish_type='{garnish_type}'")
        else:
            self.ingredient_constraints["garnish_type"] = [f"@garnish_type='{garnish_type}'"]
        return self

    def build(self):
        constraints = "./category"
        if self.category_constraints:
            cat_constraints = str.join(" ", self.category_constraints)
            constraints += f"[{cat_constraints}]"
        constraints += "/glass"
        if self.glass_constraint:
            glass_constraint = str.join(" ", self.glass_constraint)
            constraints += f"[{glass_constraint}]"
        constraints += "/cocktails/cocktail"
        if self.ingredient_constraints:
            for attr, values in self.ingredient_constraints.items():
                constraints += f"[descendant::ingredient[{' '.join(values)}]]"
            # ingredient_constraints = str.join(" ", self.ingredient_constraints)
            # constraints += f"[{ingredient_constraints}]"

        return constraints


if __name__ == "__main__":
    cl = CaseLibrary()
    constraints = ConstraintsBuilder().or_alc_type("rum").or_alc_type("creamy liqueur").or_basic_taste("cream")
    print(constraints.build())
    print(cl.findall(constraints))
    # print(cl.findall(
    #     "./category/glass//cocktail[descendant::ingredient[@alc_type='rum' or @alc_type='creamy liqueur']][descendant::ingredient[@basic_taste='cream']]"))
