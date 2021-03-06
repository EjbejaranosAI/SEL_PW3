import pytest

from src.cbr.case_library import ConstraintsBuilder


@pytest.fixture
def builder():
    return ConstraintsBuilder()


def test_filter_category(builder):
    builder.filter_category(include="cat1", exclude="cat2").filter_category(include=["cat3"]).filter_category(
        exclude=["cat4"]
    ).filter_category(include=["cat5", "cat6"], exclude=["cat7", "cat8"])
    assert ["@type='cat1'", "or @type='cat3'", "or @type='cat5'", "or @type='cat6'"] == builder.include_categories and [
        "@type!='cat2'",
        "or @type!='cat4'",
        "or @type!='cat7'",
        "or @type!='cat8'",
    ] == builder.exclude_categories


def test_filter_glass(builder):
    builder.filter_glass(include=["shot", "cup"], exclude=["martini glass", "hurricane glass"])
    assert ["@type='shot'", "or @type='cup'"] == builder.include_glasses and [
        "@type!='martini glass'",
        "or @type!='hurricane glass'",
    ] == builder.exclude_glasses


# TODO
def test_filter_alc_type(builder):
    assert False


# TODO
def test_filter_taste(builder):
    assert False


# TODO
def test_filter_garnish_type(builder):
    assert False


def test_filter_ingredient(builder):
    builder.filter_ingredient(include=["sugar", "orange juice"], exclude="banana")
    assert ["text()='sugar'", "and text()='orange juice'"] == builder.ingredient_constraints["ingredient"][
        "include"
    ] and ["text()!='banana'"] == builder.ingredient_constraints["ingredient"]["exclude"]


def test_search_all_cocktails(builder):
    assert builder.build() == "./category/glass//cocktail"


def test_build(builder):
    builder.filter_category(include="cocktail", exclude="beer").filter_glass(include="martini glass").filter_alc_type(
        include=["rum", "creamy liqueur"]
    ).filter_taste(include="cream").filter_garnish_type(exclude="leaf(ves)").filter_ingredient(
        include=["banana", "cherry"], exclude="chocolate"
    )
    assert (
        builder.build()
        == "./category[@type='cocktail'][@type!='beer']/glass[@type='martini glass']//cocktail[descendant::ingredient[@alc_type='rum' and @alc_type='creamy liqueur']][descendant::ingredient[@basic_taste='cream']][descendant::ingredient[@garnish_type!='leaf(ves)']][descendant::ingredient[text()='banana']][descendant::ingredient[text()='cherry']][descendant::ingredient[text()!='chocolate']]"
    )
