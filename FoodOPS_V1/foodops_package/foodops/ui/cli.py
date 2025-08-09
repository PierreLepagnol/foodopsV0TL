from ..core import create_restaurants
from ..core.game import Game

def main():
    print("=== Bienvenue dans FoodOps (marché par segments) 🎮🍽️ ===\n")
    print("Règles finance (💲) : Apport 50k€ • Banque max 250k€ (Taux annuel 3%) • BPI 20k€ (Taux annuel 0%).\n")
    print("Pour commencer, nous allons créer les restaurants des joueurs, attention à votre trésorerie de départ.")
    print("Chaque tour, les joueurs prennent des décisions qui auront un impact sur leurs résultats.")

    # On ne passe plus de paramètre ici
    restaurants = create_restaurants()

    game = Game(restaurants=restaurants)
    game.play()

if __name__ == "__main__":
    main()
# foodops/ui/cli.py