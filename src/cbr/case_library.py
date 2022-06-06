from typing import Dict, List, Union

from lxml import etree, objectify

from definitions import CASE_LIBRARY


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
    constraints_dict = include_dict.get(key, {key: []})

    if key != "ingredient":
        search_key = f"@{key}"
    else:
        search_key = "text()"

    if is_exclusion:
        include_constraints = constraints_dict.get("exclude", [])
    else:
        include_constraints = constraints_dict.get("include", [])
    if include_constraints:
        if isinstance(elements, str):
            if is_exclusion:
                include_constraints.append(f"and {search_key}!='{elements}'")
            else:
                include_constraints.append(f"and {search_key}='{elements}'")
        else:
            if is_exclusion:
                for inclusion in elements:
                    include_constraints.append(f"and {search_key}!='{inclusion}'")
            else:
                for inclusion in elements:
                    include_constraints.append(f"and {search_key}='{inclusion}'")
    else:
        include_dict[key] = constraints_dict
        if isinstance(elements, str):
            if is_exclusion:
                include_dict[key]["exclude"] = [f"{search_key}!='{elements}'"]
            else:
                include_dict[key]["include"] = [f"{search_key}='{elements}'"]
        else:
            if is_exclusion:
                include_dict[key]["exclude"] = [f"{search_key}!='{elements[0]}'"]
                if len(elements) > 1:
                    include_constraints = include_dict[key]["exclude"]
                    for inclusion in elements[1:]:
                        include_constraints.append(f"and {search_key}!='{inclusion}'")
            else:
                include_dict[key]["include"] = [f"{search_key}='{elements[0]}'"]
                if len(elements) > 1:
                    include_constraints = include_dict[key]["include"]
                    for inclusion in elements[1:]:
                        include_constraints.append(f"and {search_key}='{inclusion}'")
    return include_dict


class CaseLibrary:
    def __init__(self, case_library_file):
        self.case_library_path = case_library_file
        self.ET = objectify.parse(self.case_library_path)
        self.case_library = self.ET.getroot()
        self.cocktails = None

    def findall(self, constraints):
        if isinstance(constraints, str):
            return self.case_library.xpath(constraints)
        elif isinstance(constraints, ConstraintsBuilder):
            return self.case_library.xpath(constraints.build())
        else:
            raise TypeError("constraints must be string or ConstraintsBuilder.")

    def remove_case(self, case):
        parent = case.getparent()
        parent.remove(case)
        self.ET.write()
        self.ET.write(self.case_library_path, pretty_print=True, encoding="utf-8")


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
        if exclude is not None:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "alc_type", exclude, is_exclusion=True
            )
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
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "basic_taste", include)
        if exclude is not None:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "basic_taste", exclude, is_exclusion=True
            )
        return self

    def filter_garnish_type(self, include=None, exclude=None):
        if include is not None:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "garnish_type", include)
        if exclude is not None:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "garnish_type", exclude, is_exclusion=True
            )
        return self

    def filter_ingredient(self, include=None, exclude=None):
        if include is not None:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "ingredient", include)
        if exclude is not None:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "ingredient", exclude, is_exclusion=True
            )
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
        constraints += "//cocktail"
        if self.ingredient_constraints:
            for attr, values in self.ingredient_constraints.items():
                if "include" in values.keys():
                    constraints += f"[descendant::ingredient[{' '.join(values['include'])}]]"
                if "exclude" in values.keys():
                    constraints += f"[descendant::ingredient[{' '.join(values['exclude'])}]]"

        return constraints
