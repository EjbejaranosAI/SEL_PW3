from typing import Dict, List, Union

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
    def __init__(self, include_dict: Dict = None, exclude_dict: Dict = None):
        self.include_dict = include_dict if include_dict else dict()
        self.exclude_dict = exclude_dict if exclude_dict else dict()

    def include(self, key: str, elements: Union[str, List[str]]):
        self.include_dict = _include_to_dict(self.include_dict, key, elements)
        return self

    def exclude(self, key: str, elements: Union[str, List[str]]):
        self.exclude_dict = _include_to_dict(self.exclude_dict, key, elements, is_exclusion=True)
        return self

    def build(self):
        include_list = []
        for key, value in self.include_dict.items():
            include_list = _include_to_list(include_list, value["include"])
        for key, value in self.exclude_dict.items():
            include_list = _include_to_list(include_list, value["include"], is_exclusion=True)

        if include_list:
            return f"//cocktail[{' and '.join(include_list)}]"
        else:
            return "//cocktail"


def _include_to_list(include_list: List[str], elements: Union[str, List[str]], is_exclusion=False):
    if include_list:
        if isinstance(elements, str):
            if is_exclusion:
                include_list.append(f"or @type!='{elements}'")
            else:
                include_list.append(f"or @type='{elements}'")
        elif is_exclusion:
            for inclusion in elements:
                include_list.append(f"or @type!='{inclusion}'")
        else:
            for inclusion in elements:
                include_list.append(f"or @type='{inclusion}'")
    else:
        if isinstance(elements, str):
            if is_exclusion:
                include_list = [f"@type!='{elements}'"]
            else:
                include_list = [f"@type='{elements}'"]
        elif is_exclusion:
            include_list = [f"@type!='{elements[0]}'"]
            if len(elements) > 1:
                for inclusion in elements[1:]:
                    include_list.append(f"or @type!='{inclusion}'")
        else:
            include_list = [f"@type='{elements[0]}'"]
            if len(elements) > 1:
                for inclusion in elements[1:]:
                    include_list.append(f"or @type='{inclusion}'")

    return include_list


def _include_to_dict(include_dict: Dict, key: str, elements: Union[str, List[str]], is_exclusion=False):
    constraints_dict = include_dict.get(key, dict())
    include_constraints = constraints_dict.get("include", [])
    if include_constraints:
        if isinstance(elements, str):
            include_constraints.append(f"or @{key}='{elements}'")
        else:
            for inclusion in elements:
                include_constraints.append(f"or @{key}='{inclusion}'")
    else:
        if isinstance(elements, str):
            include_dict[key] = {"include": [f"@{key}='{elements}'"]}
        else:
            include_dict[key] = {"include": [f"@{key}='{elements[0]}'"]}
            if len(elements) > 1:
                include_constraints = include_dict[key]["include"]
                for inclusion in elements[1:]:
                    include_constraints.append(f"or @{key}='{inclusion}'")

    return include_dict





class ConstraintsBuilder:
    def __init__(self, include_category="", include_glass=""):
        self.constraints = "./"
        if include_category:
            self.include_category = [f"@type='{include_category}'"]
        else:
            self.include_category = []
        if include_glass:
            self.include_glass = [f"@type='{include_glass}'"]
        else:
            self.include_glass = []
        self.exclude_category = []
        self.exclude_glass = []
        self.ingredient_constraints = dict()

    def filter_category(self, include: Union[str, List[str], None] = None, exclude: Union[str, List[str], None] = None):
        if include is not None:
            self.include_category = _include_to_list(self.include_category, include)

        if exclude is not None:
            self.exclude_category = _include_to_list(self.exclude_category, exclude, is_exclusion=True)

        return self

    def filter_glass(self, include: Union[str, List[str], None] = None, exclude: Union[str, List[str], None] = None):
        if include is not None:
            self.include_glass = _include_to_list(self.include_glass, include)

        if exclude is not None:
            self.exclude_glass = _include_to_list(self.exclude_glass, exclude, is_exclusion=True)

        return self

    # def and_alc_type(self, alc_type):
    #     alc_constraints = self.ingredient_constraints.get('alc_type', [])
    #     if alc_constraints:
    #         alc_constraints.append((f"and @acl_type='{alc_type}'"))
    #     else:
    #         alc_constraints.append([f"@alc_type='{alc_type}'"])
    #     return self

    def filter_alc_type(self, include=None, exclude=None):
        if include is not None:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "alc_type", include)
            # alc_constraints = self.ingredient_constraints.get("alc_type", dict())
            # include_constraints = alc_constraints.get('include', [])
            # if include_constraints:
            #     if isinstance(include, str):
            #         include_constraints.append(f"or @acl_type='{include}'")
            #     else:
            #         for inclusion in include:
            #             include_constraints.append(f"or @acl_type='{inclusion}'")
            # else:
            #     if isinstance(include, str):
            #         self.ingredient_constraints["alc_type"] = {"include": [f"@alc_type='{include}'"]}
            #     else:
            #         self.ingredient_constraints["alc_type"] = {"include": [f"@alc_type='{include[0]}'"]}
            #         if len(include) > 1:
            #             for inclusion in include:
            #                 include_constraints.append(f"or @acl_type='{inclusion}'")

        if exclude is not None:
            alc_constraints = self.ingredient_constraints.get("alc_type", dict())
            exclude_constraints = alc_constraints.get("exclude", [])
            if exclude_constraints:
                exclude_constraints.append(f"or @acl_type!='{exclude}'")
            elif alc_constraints:
                self.ingredient_constraints["alc_type"]["exclude"] = [f"@alc_type!='{exclude}'"]
            else:
                self.ingredient_constraints["alc_type"] = {"exclude": [f"@alc_type!='{exclude}'"]}

        return self

    # def and_basic_taste(self, basic_taste):
    #     taste_constraints = self.ingredient_constraints.get('basic_taste', [])
    #     if taste_constraints:
    #         taste_constraints.append(f"and @basic_taste='{basic_taste}'")
    #     else:
    #         taste_constraints.append([f"@basic_taste='{basic_taste}'"])
    #     return self

    def filter_taste(self, include=None, exclude=None):
        if include is not None:
            taste_constraints = self.ingredient_constraints.get("basic_taste", dict())
            include_constraints = taste_constraints.get("include", [])
            if include_constraints:
                include_constraints.append(f"or @basic_taste='{include}'")
            else:
                self.ingredient_constraints["basic_taste"] = {"include": [f"@basic_taste='{include}'"]}

        if exclude is not None:
            taste_constraints = self.ingredient_constraints.get("basic_taste", dict())
            exclude_constraints = taste_constraints.get("exclude", [])
            if exclude_constraints:
                exclude_constraints.append(f"or @basic_taste!='{exclude}'")
            else:
                self.ingredient_constraints["basic_taste"] = {"exclude": [f"@basic_taste!='{exclude}'"]}

        return self

    def filter_garnish_type(self, include=None, exclude=None):
        if include is not None:
            garnish_constraints = self.ingredient_constraints.get("garnish_type", dict())
            include_constraints = garnish_constraints.get("include", [])
            if include_constraints:
                include_constraints.append(f"or @garnish_type='{include}'")
            else:
                self.ingredient_constraints["garnish_type"] = {"include": [f"@garnish_type='{include}'"]}

        if exclude is not None:
            garnish_constraints = self.ingredient_constraints.get("garnish_type", dict())
            exclude_constraints = garnish_constraints.get("exclude", [])
            if exclude_constraints:
                exclude_constraints.append(f"or @garnish_type!='{exclude}'")
            else:
                self.ingredient_constraints["garnish_type"] = {"exclude": [f"@garnish_type!='{exclude}'"]}

        return self

    def build(self):
        constraints = "./category"
        if self.include_category:
            cat_constraints = str.join(" ", self.include_category)
            constraints += f"[{cat_constraints}]"
        if self.exclude_category:
            cat_constraints = str.join(" ", self.exclude_category)
            constraints += f"[{cat_constraints}]"
        constraints += "/glass"
        if self.include_glass:
            glass_constraint = str.join(" ", self.include_glass)
            constraints += f"[{glass_constraint}]"
        if self.exclude_glass:
            glass_constraint = str.join(" ", self.exclude_glass)
            constraints += f"[{glass_constraint}]"
        constraints += "/cocktails/cocktail"
        if self.ingredient_constraints:
            for attr, values in self.ingredient_constraints.items():
                if "include" in values.keys():
                    constraints += f"[descendant::ingredient[{' '.join(values['include'])}]]"
                if "exclude" in values.keys():
                    constraints += f"[descendant::ingredient[{' '.join(values['exclude'])}]]"

        return constraints


if __name__ == "__main__":
    cl = CaseLibrary()
    constraints = (
        ConstraintsBuilder()
        .filter_category(include="ordinary drink", exclude="shot")
        .filter_alc_type(include=["creamy liqueur", "vodka"], exclude="rum")
        .filter_taste(include="cream")
    )
    # constraints = ConstraintsBuilder().filter_category(include=["ordinary drink", "shot"])
    print(constraints.build())
    print(cl.findall(constraints))
    # print(cl.findall(
    #     "./category/glass//cocktail[descendant::ingredient[@alc_type='rum' or @alc_type='creamy liqueur']][descendant::ingredient[@basic_taste='cream']]"))
