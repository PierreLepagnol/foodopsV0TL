from FoodOPS_V1.core.game import Game, initialisation_restaurants_auto
from FoodOPS_V1.domain.scenario import CATALOG_SCENARIOS


def run():
    restaurants_list = initialisation_restaurants_auto(nb_joueurs=2)
    game = Game(
        restaurants=restaurants_list, scenario=CATALOG_SCENARIOS["centre_ville"]
    )
    game.play()


if __name__ == "__main__":
    run()
