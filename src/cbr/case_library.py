from typing import Dict, List, Union

from lxml import objectify

from src.entity.query import Query


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
        append_search_key = f"and {search_key}"
    else:
        search_key = "text()"
        append_search_key = search_key

    if is_exclusion:
        include_constraints = constraints_dict.get("exclude", [])
    else:
        include_constraints = constraints_dict.get("include", [])
    if include_constraints:
        if isinstance(elements, str):
            if is_exclusion:
                include_constraints.append(f"{append_search_key}!='{elements}'")
            else:
                include_constraints.append(f"{append_search_key}='{elements}'")
        else:
            if is_exclusion:
                for inclusion in elements:
                    include_constraints.append(f"{append_search_key}!='{inclusion}'")
            else:
                for inclusion in elements:
                    include_constraints.append(f"{append_search_key}='{inclusion}'")
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
                        include_constraints.append(f"{append_search_key}!='{inclusion}'")
            else:
                include_dict[key]["include"] = [f"{search_key}='{elements[0]}'"]
                if len(elements) > 1:
                    include_constraints = include_dict[key]["include"]
                    for inclusion in elements[1:]:
                        include_constraints.append(f"{append_search_key}='{inclusion}'")
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

    drink_types: list of str
        Sorted list of the available drink types.

    glass_types: list of str
        Sorted list of the available glass types.

    alc_types: list of str
        Sorted list of the available alcohol types.

    taste_types: list of str
        Sorted list of the available basic tastes.

    garnish_types: list of str
        Sorted list of the available garnish types.

    ingredients: list of str
        Sorted list of the available ingredients.

    value_counter: dict
        Counter for each of the available values in the case library.

    ingredients_onto: dict
        Ontology of ingredients

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
        self.drink_types = list()
        self.glass_types = list()
        self.alc_types = list()
        self.taste_types = list()
        self.garnish_types = list()
        self.ingredients = list()
        self.value_counter = dict()
        self.ingredients_onto = {"alcoholic": dict(), "non-alcoholic": dict()}
        self.initialize_type_sets()

    def findall(self, constraints):
        """
        Find all the cases matching a constraint.

        Parameters
        ----------
        constraints: str or ConstraintsBuilder
            The constraints to search for cases. It can be a string with a complex search pattern for XPath search or a
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

    def add_case(self, case):
        """
        Add a case from the case library. The new case will obtain a unique ID before being added to the case library.

        After adding the case the XML file is updated.

        Parameters
        ----------
        case : :class:`lxml.objectify.ObjectifiedElement`
            The case to add to the case library.
        """
        drink_type = case.category
        glass_type = case.glass
        parent = self.case_library.find(f"./category[@type='{drink_type}']/glass[@type='{glass_type}']")
        case.derivation = "adapted"
        parent.append(case)
        self.ET.write(self.case_library_path, pretty_print=True, encoding="utf-8")

        self._increase_counter(glass_type, "glass_types")
        self._increase_counter(drink_type, "drink_types")
        for ingredient in case.ingredients.iterchildren():
            name = ingredient.text
            self._increase_counter(name, "ingredients")
            alc_type = ingredient.attrib["alc_type"]
            if alc_type:
                self._increase_counter(alc_type, "alc_types")
            basic_taste = ingredient.attrib["basic_taste"]
            if basic_taste:
                self._increase_counter(basic_taste, "taste_types")
            garnish_type = ingredient.attrib["garnish_type"]
            if garnish_type:
                self._increase_counter(garnish_type, "garnish_types")

    def remove_case(self, case):
        """
        Remove a case from the case library.

        After removing the case the XML file is updated.

        Parameters
        ----------
        case : :class:`lxml.objectify.ObjectifiedElement`
            The case to remove from the case library
        """
        category = case.category
        self._decrease_counter(category, self.drink_types, "drink_types")
        glass = case.glass
        self._decrease_counter(glass, self.glass_types, "glass_types")

        for ingredient in case.ingredients.iterchildren():
            name = ingredient.text
            self._decrease_counter(name, self.ingredients, "ingredients")
            alc_type = ingredient.attrib["alc_type"]
            if alc_type:
                self._decrease_counter(alc_type, self.alc_types, "alc_types")
            basic_taste = ingredient.attrib["basic_taste"]
            if basic_taste:
                self._decrease_counter(basic_taste, self.taste_types, "taste_types")
            garnish_type = ingredient.attrib["garnish_type"]
            if garnish_type:
                self._decrease_counter(garnish_type, self.garnish_types, "garnish_types")

        parent = case.getparent()
        parent.remove(case)
        self.ET.write(self.case_library_path, pretty_print=True, encoding="utf-8")

    def _decrease_counter(self, key, value_list, types):
        self.value_counter[types][key] -= 1
        if self.value_counter[types][key] == 0:
            value_list.remove(key)
            self.value_counter[types].pop(key)

    def _increase_counter(self, key, types):
        self.value_counter[types][key] += 1

    def initialize_type_sets(self):
        drink_types = set()
        glass_types = set()
        ingredients = set()
        alc_types = set()
        taste_types = set()
        garnish_types = set()
        value_counter = dict(
            drink_types={}, glass_types={}, ingredients={}, alc_types={}, taste_types={}, garnish_types={}
        )
        for cocktail in self.case_library.xpath(".//cocktail"):
            drink = cocktail.category.text
            glass = cocktail.glass.text
            if drink in value_counter["drink_types"].keys():
                value_counter["drink_types"][drink] += 1
            else:
                value_counter["drink_types"][drink] = 1
                drink_types.add(drink)

            if glass in value_counter["glass_types"].keys():
                value_counter["glass_types"][glass] += 1
            else:
                value_counter["glass_types"][glass] = 1
                glass_types.add(glass)

            for ingredient in cocktail.ingredients.iterchildren():
                name = ingredient.text
                if name in value_counter["ingredients"].keys():
                    value_counter["ingredients"][name] += 1
                else:
                    value_counter["ingredients"][name] = 1
                    ingredients.add(name)

                alc_type = ingredient.attrib["alc_type"]
                basic_taste = ingredient.attrib["basic_taste"]
                garnish_type = ingredient.attrib["garnish_type"]
                if alc_type:
                    if alc_type in value_counter["alc_types"].keys():
                        value_counter["alc_types"][alc_type] += 1
                    else:
                        value_counter["alc_types"][alc_type] = 1
                        alc_types.add(alc_type)
                    if alc_type in self.ingredients_onto["alcoholic"].keys():
                        self.ingredients_onto["alcoholic"][name] = alc_type
                    else:
                        self.ingredients_onto["alcoholic"][name] = alc_type
                elif basic_taste:
                    if basic_taste in value_counter["taste_types"].keys():
                        value_counter["taste_types"][basic_taste] += 1
                    else:
                        value_counter["taste_types"][basic_taste] = 1
                        taste_types.add(basic_taste)
                    if basic_taste in self.ingredients_onto["non-alcoholic"].keys():
                        self.ingredients_onto["non-alcoholic"][name] = basic_taste
                    else:
                        self.ingredients_onto["non-alcoholic"][name] = basic_taste
                if garnish_type:
                    if garnish_type in value_counter["garnish_types"].keys():
                        value_counter["garnish_types"][garnish_type] += 1
                    else:
                        value_counter["garnish_types"][garnish_type] = 1
                        garnish_types.add(garnish_type)

        self.drink_types = sorted(drink_types)
        self.glass_types = sorted(glass_types)
        self.alc_types = sorted(alc_types)
        self.taste_types = sorted(taste_types)
        self.garnish_types = sorted(garnish_types)
        self.ingredients = sorted(ingredients)
        self.value_counter = value_counter


class ConstraintsBuilder:
    """
    A builder for the constraints used in :meth:`CaseLibrary.findall`.

    Parameters
    ----------
    include_category : str, default ""
        A drink category to include in the search.

    include_glass : str, default ""
        A glass type to include in the search.

    Attributes
    ----------
    constraints : str
        The search pattern with the constraints.

    include_categories : list of str
        The list of drink categories to include in the search.

    exclude_categories : list of str
        The list of drink categories to exclude in the search.

    include_glasses : list of str
        The list of glass types to include in the search.

    exclude_glasses : list of str
        The list of glass types to exclude in the search.

    ingredient_constraints : dict of dict of list of str
        The constraints applied to the ingredients.

    Examples
    --------
    You can chain multiple filters of the same or different types.
    >>> from definitions import CASE_LIBRARY_FILE
    >>> from src.cbr.case_library import ConstraintsBuilder, CaseLibrary
    >>> case_library = CaseLibrary(CASE_LIBRARY_FILE)
    >>> builder = ConstraintsBuilder(include_category="cocktail", include_glass="hurricane glass")
    ...     .filter_alc_type(include="rum").filter_taste(include="sweet")
    ...     .filter_ingredient(include=["banana", "sugar"], exclude="coffee")
    >>> cocktails = case_library.findall(builder)
    """

    def __init__(self, include_category="", include_glass=""):
        self.constraints = "./"
        if include_category:
            self.include_categories = [f"@type='{include_category}'"]
        else:
            self.include_categories = []
        if include_glass:
            self.include_glasses = [f"@type='{include_glass}'"]
        else:
            self.include_glasses = []
        self.exclude_categories = []
        self.exclude_glasses = []
        self.ingredient_constraints = dict()

    def filter_category(self, include: Union[str, List[str], None] = None, exclude: Union[str, List[str], None] = None):
        """
        Add a filter for the cocktail category.

        Parameters
        ----------
        include : str or list of str or None, default None
            Categories that the cases must include.

        exclude : str or list of str or None, default None
            Categories that the cases must not include.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.

        Examples
        --------
        Add multime conditions at the same time.

        >>> builder = ConstraintsBuilder().filter_category(include="ordinary drink", exclude=["shot", "cocktail"])

        Add only inclusion or exclusions.

        >>> builder = ConstraintsBuilder().filter_category(include="ordinary drink")
        >>> builder.filter_category(exclude=["shot", "cocktail"])
        """

        if include is not None and len(include) > 0:
            self.include_categories = _include_to_list(self.include_categories, include)

        if exclude is not None and len(exclude) > 0:
            self.exclude_categories = _include_to_list(self.exclude_categories, exclude, is_exclusion=True)

        return self

    def filter_glass(self, include: Union[str, List[str], None] = None, exclude: Union[str, List[str], None] = None):
        """
        Add a filter for the glass type.

        Parameters
        ----------
        include : str or list of str or None, default None
            Glass types that the cases must include.

        exclude : str or list of str or None, default None
            Glass types that the cases must not include.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.

        Examples
        --------
        Add multime conditions at the same time.

        >>> builder = ConstraintsBuilder().filter_glass(include="shot glass",
        ...     exclude=["hurricane glass", "martini glass"])

        Add only inclusion or exclusions.

        >>> builder = ConstraintsBuilder().filter_glass(include="shot glass")
        >>> builder.filter_glass(exclude=["hurricane glass", "martini glass"])
        """
        if include is not None and len(include) > 0:
            self.include_glasses = _include_to_list(self.include_glasses, include)

        if exclude is not None and len(exclude) > 0:
            self.exclude_glasses = _include_to_list(self.exclude_glasses, exclude, is_exclusion=True)

        return self

    def filter_alc_type(self, include=None, exclude=None):
        """
        Add a filter for the alcohol type.

        Parameters
        ----------
        include : str or list of str or None, default None
            Alcohol types that the cases must include.

        exclude : str or list of str or None, default None
            Alcohol types that the cases must not include.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.

        Examples
        --------
        Add multime conditions at the same time.

        >>> builder = ConstraintsBuilder().filter_alc_type(include="gin", exclude=["rum", "vodka"])

        Add only inclusion or exclusions.

        >>> builder = ConstraintsBuilder().filter_alc_type(include="gin")
        >>> builder.filter_alc_type(exclude=["rum", "vodka"])
        """
        if include is not None and len(include) > 0:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "alc_type", include)
        if exclude is not None and len(exclude) > 0:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "alc_type", exclude, is_exclusion=True
            )
        return self

    def filter_taste(self, include=None, exclude=None):
        """
        Add a filter for the basic taste type.

        Parameters
        ----------
        include : str or list of str or None, default None
            Basic taste types that the cases must include.

        exclude : str or list of str or None, default None
            Basic taste types that the cases must not include.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.

        Examples
        --------
        Add multime conditions at the same time.

        >>> builder = ConstraintsBuilder().filter_taste(include="sweet", exclude=["sour", "salty"])

        Add only inclusion or exclusions.

        >>> builder = ConstraintsBuilder().filter_taste(include="sweet")
        >>> builder.filter_taste(exclude=["sour", "salty"])
        """
        if include is not None and len(include) > 0:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "basic_taste", include)
        if exclude is not None and len(exclude) > 0:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "basic_taste", exclude, is_exclusion=True
            )
        return self

    def filter_garnish_type(self, include=None, exclude=None):
        """
        Add a filter for the garnish type.

        Parameters
        ----------
        include : str or list of str or None, default None
            Garnish types that the cases must include.

        exclude : str or list of str or None, default None
            Garnish types that the cases must not include.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.

        Examples
        --------
        Add multime conditions at the same time.

        >>> builder = ConstraintsBuilder().filter_garnish_type(include="slice", exclude="berry")

        Add only inclusion or exclusions.

        >>> builder = ConstraintsBuilder().filter_garnish_type(include="slice")
        >>> builder.filter_garnish_type(exclude=["berry", "wedge"])
        """
        if include is not None and len(include) > 0:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "garnish_type", include)
        if exclude is not None and len(exclude) > 0:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "garnish_type", exclude, is_exclusion=True
            )
        return self

    def filter_ingredient(self, include=None, exclude=None):
        """
        Add a filter for the ingredient name.

        Parameters
        ----------
        include : str or list of str or None, default None
            Ingredients that the cases must include.

        exclude : str or list of str or None, default None
            Ingredients that the cases must not include.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.

        Examples
        --------
        Add multime conditions at the same time.

        >>> builder = ConstraintsBuilder().filter_ingredient(include="banana", exclude="strawberry")

        Add only inclusion or exclusions.

        >>> builder = ConstraintsBuilder().filter_ingredient(include="banana")
        >>> builder.filter_garnish_type(exclude=["strawberry", "coffee"])
        """
        if include is not None and len(include) > 0:
            self.ingredient_constraints = _include_to_dict(self.ingredient_constraints, "ingredient", include)
        if exclude is not None and len(exclude) > 0:
            self.ingredient_constraints = _include_to_dict(
                self.ingredient_constraints, "ingredient", exclude, is_exclusion=True
            )
        return self

    def build(self):
        """
        Build the `ConstraintsBuilder`.

        Returns
        -------
        constraints: str
            An XPath pattern with the constraints.
        """
        constraints = "./category"
        if self.include_categories:
            cat_constraints = str.join(" ", self.include_categories)
            constraints += f"[{cat_constraints}]"
        if self.exclude_categories:
            cat_constraints = str.join(" ", self.exclude_categories)
            constraints += f"[{cat_constraints}]"
        constraints += "/glass"
        if self.include_glasses:
            glass_constraint = str.join(" ", self.include_glasses)
            constraints += f"[{glass_constraint}]"
        if self.exclude_glasses:
            glass_constraint = str.join(" ", self.exclude_glasses)
            constraints += f"[{glass_constraint}]"
        constraints += "//cocktail"
        if self.ingredient_constraints:
            for attr, values in self.ingredient_constraints.items():
                if attr != "ingredient":
                    if "include" in values.keys():
                        constraints += f"[descendant::ingredient[{' '.join(values['include'])}]]"
                    if "exclude" in values.keys():
                        constraints += f"[descendant::ingredient[{' '.join(values['exclude'])}]]"
                else:
                    if "include" in values.keys():
                        for value in values["include"]:
                            constraints += f"[descendant::ingredient[{value}]]"
                    if "exclude" in values.keys():
                        for value in values["exclude"]:
                            constraints += f"[descendant::ingredient[{value}]]"

        return constraints

    def from_query(self, query: Query):
        """
        Adds filters to the ConstraintsBuilder from a :class:`Query`.

        Parameters
        ----------
        query : `entity.query.Query`
            The query from where to extract the filters.

        Returns
        -------
        self : ConstraintsBuilder
            The ConstraintsBuilder.
        """

        return (
            self.filter_category(include=query.category)
            .filter_glass(include=query.glass)
            .filter_alc_type(include=query.alc_types)
            .filter_taste(include=query.basic_tastes)
            .filter_ingredient(include=query.ingredients, exclude=query.exc_ingredients)
        )
