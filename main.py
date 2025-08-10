from FoodOPS_V1.core.game import Game, initialisation_restaurants
from FoodOPS_V1.domain.local import CATALOG_LOCALS
from FoodOPS_V1.domain.restaurant import Restaurant, RestaurantType

from FoodOPS_V1.domain.scenario import CATALOG_SCENARIOS
from FoodOPS_V1.rules.recipe_factory import build_menu_for_type


def run():
    type_restaurant = RestaurantType.BISTRO
    local = CATALOG_LOCALS[0]
    restaurant = Restaurant(
        name="Demo Resto",
        type=type_restaurant,
        local=local,
        funds=20000.0,
        marketing_budget=300.0,
    )
    restaurant.menu = build_menu_for_type(type_restaurant)
    scenario = CATALOG_SCENARIOS["centre_ville"]

    restaurants_list = initialisation_restaurants()
    game = Game(restaurants=restaurants_list, scenario=scenario)
    game.play()


if __name__ == "__main__":
    run()
