import uuid
from typing import Dict, List, Union

from lxml import objectify


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
    """
    Case library for the CBR.

    Parameters
    ----------
    case_library_file: str
        Path to the case library file.

    Attributes
    ----------
    case_library_file : str
        Path to the case library file.

    ET: lxml ElementTree
        Element tree representing the case library.

    case_library: lxml ObjectifiedElement
        Root of the case library.

    drink_types: set of str
        Set of the available drink types.

    glass_types: set of str
        Set of the available glass types.

    alc_types: set of str
        Set of the available alcohol types.

    taste_types: set of str
        Set of the available basic tastes.

    garnish_types: set of str
        Set of the available garnish types.

    ingredients: set of str
        Set of the available ingredients.

    See Also
    --------
    CaseLibrary.findall : Find all the cases matching a constraint.
    CaseLibrary.remove_case: Remove a case from the case library.
    CaseLibrary.add_case: Add a case to the case library.
    """

    def __init__(self, case_library_file):
        self.case_library_path = case_library_file
        self.ET = objectify.parse(self.case_library_path)
        self.case_library = self.ET.getroot()
        self.drink_types = set()
        self.glass_types = set()
        self.alc_types = set()
        self.taste_types = set()
        self.garnish_types = set()
        self.ingredients = set()
        self._initialize_type_sets()

    def findall(self, constraints):
        """
        Find all the cases matching a constraint.

        Parameters
        ----------
        constraints: str or ConstraintsBuilder
            The constraints to search for cases. It can be a string with a complex search pattern or a
            ConstraintsBuilder object.

        Returns
        -------
        cases : list of :class:`lxml.objectify.ObjectifiedElement`
            A list of cases that match the given constraint.

        See Also
        --------
        :class:`ConstraintsBuilder` : A builder for the constraints used in :meth:`CaseLibrary.findall`.
        """
        if isinstance(constraints, str):
            return self.case_library.xpath(constraints)
        elif isinstance(constraints, ConstraintsBuilder):
            return self.case_library.xpath(constraints.build())
        else:
            raise TypeError("constraints must be string or ConstraintsBuilder.")

    def remove_case(self, case):
        """
        Remove a case from the case library.

        After removing the case the XML file is updated.

        Parameters
        ----------
        case : :class:`lxml.objectify.ObjectifiedElement`
            The case to remove from the case library
        """
        parent = case.getparent()
        parent.remove(case)
        self.ET.write(self.case_library_path, pretty_print=True, encoding="utf-8")

    def add_case(self, case):
        """
        Add a case from the case library.

        After adding the case the XML file is updated.

        Parameters
        ----------
        case : :class:`lxml.objectify.ObjectifiedElement`
            The case to add to the case library.
        """
        drink_type = case.category
        glass_type = case.glass
        parent = self.case_library.find(f"./category[@type='{drink_type}']/glass[@type='{glass_type}']")
        case.set("id", str(uuid.uuid1().int))
        parent.append(case)

    def _initialize_type_sets(self):
        self.drink_types = set(self.case_library.xpath("./category/@type"))
        self.glass_types = set(self.case_library.xpath(".//glass/@type"))
        self.alc_types = set(self.case_library.xpath(".//ingredient/@alc_type"))
        self.alc_types.remove("")
        self.taste_types = set(self.case_library.xpath(".//ingredient/@basic_taste"))
        self.taste_types.remove("")
        self.garnish_types = set(self.case_library.xpath(".//ingredient/@garnish_type"))
        self.garnish_types.remove("")
        self.ingredients = set(self.case_library.xpath(".//ingredient/text()"))


class ConstraintsBuilder:
    """A builder for the constraints used in :meth:`CaseLibrary.findall`.

    Parameters
    ----------
    include_category : str, optional
        A drink category to include in the search.

    include_glass : str, optional
        A glass type to include in the search.

    Attributes
    ----------
    constraints : str
        The search pattern with the constraints.

    include_category : list of str
        The list of drink categories to include in the search.

    exclude_category : list of str
        The list of drink categories to exclude in the search.

    include_glass : list of str
        The list of glass types to include in the search.

    exclude_glass : list of str
        The list of glass types to exclude in the search.

    ingredient_constraints : dict of dict of list of str

    Examples
    --------
    >>> from definitions import CASE_LIBRARY
    >>> from src.cbr.case_library import ConstraintsBuilder, CaseLibrary
    >>> case_library = CaseLibrary(CASE_LIBRARY)
    >>> builder = ConstraintsBuilder()
    >>> builder.filter_category().filter_glass(include="hurricane glass").filter_alc_type(include=["rum"])
    ...     .filter_taste(include="sweet")
    >>> cocktails = case_library.findall(builder)
    """

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

    def filter_alc_type(self, include=None, exclude=None):
        if include is not None:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "alc_type", include)
        if exclude is not None:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "alc_type", exclude, is_exclusion=True
            )
        return self

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
