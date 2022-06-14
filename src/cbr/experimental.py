from entity.query import Query
from src.cbr.cbr import CBR

if __name__ == "__main__":
    cbr = CBR()
    query = Query()
    query.category = "cocktail"
    query.glass = "hurricane glass"
    query.alc_types = ["vodka"]
    query.basic_tastes = ["bitter"]
    query.ingredients = ["strawberries", "vodka"]
    query.exc_ingredients = ["mint", "gin", "lemon"]
    cbr.run_query(query, "New recipe")
    cbr.forget_case()
