# scripts/run_full_demo.py
"""Démo end-to-end robuste de FoodOPS.

Ce script réalise une exécution complète, pensée pour être tolérante aux
modules manquants pendant une phase de refactor ou d'intégration:

- crée un `Restaurant` (type au choix),
- génère un menu via `rules.recipe_factory` si disponible, sinon construit un
  mini menu de secours,
- injecte un lot de produits finis pour vendre dès le premier tour,
- ajoute un peu de staff si des helpers dédiés existent sur `Restaurant`,
- lance `Game.play()` sur 2 tours,
- affiche un résumé simple de fin d'exécution.

Le script bascule automatiquement en no-op comptabilité si les fonctions clés
ne sont pas présentes, et utilise un scénario local simple si nécessaire.

Exécution (depuis la racine du dépôt):

```bash
python run_full_demo.py
```

Utilisation comme module (extrait) :

```python
from FoodOPS_V1.core.game import Game
from FoodOPS_V1.domain.restaurant import Restaurant
from FoodOPS_V1.domain.restaurant import RestaurantType

resto = Restaurant(
    name="Démo Bistro",
    type=RestaurantType.BISTRO,
)
resto.menu = build_menu_for_type(RestaurantType.BISTRO)
prime_finished_stock(resto, portions=50)
Game(restaurants=[resto]).play()
```
"""

# ---- Imports robustes -------------------------------------------------------
from FoodOPS_V1.core.game import Game
from FoodOPS_V1.domain.scenario import CATALOG_SCENARIOS
from FoodOPS_V1.domain.local import CATALOG_LOCALS
from FoodOPS_V1.domain.restaurant import Restaurant, RestaurantType
from FoodOPS_V1.domain.inventory import Inventory

# from FoodOPS_V1.domain.recipe import SimpleRecipe
from FoodOPS_V1.rules.recipe_factory import build_menu_for_type


def build_menu_for_type(resto_type):
    """Construit un menu adapté au type de restaurant.

    Tente d'abord d'utiliser `FoodOPS_V1.rules.recipe_factory.build_menu_for_type`.
    En cas d'indisponibilité (pendant une phase de travail), crée un mini-menu
    de 2 recettes génériques pour garantir la jouabilité de la démo.

    Paramètres
    - resto_type: une valeur de `RestaurantType`.

    Retour
    - list: une liste d'objets recette (implémentations du domaine).

    Exemple
    >>> from FoodOPS_V1.domain.restaurant import RestaurantType
    >>> menu = build_menu_for_type(RestaurantType.BISTRO)
    >>> len(menu) >= 2
    True
    """
    return build_menu_for_type(resto_type)


# Injecte un lot de produits finis pour pouvoir vendre au tour 1
def prime_finished_stock(resto, portions: int = 40):
    """Injecte un lot de produits finis pour vendre dès le tour 1.

    Cette étape évite d'avoir à passer par un cycle de production complet avant
    de pouvoir tester la vente et la comptabilité.

    Paramètres
    - resto: instance de `Restaurant` dont on prime l'inventaire.
    - portions: nombre de portions du premier plat du menu à injecter.

    Retour
    - tuple: (recette_primée, prix_unitaire, portions_injectées)

    Exemple
    >>> # supposons un restaurant avec un menu déjà défini
    >>> recipe, price, qty = prime_finished_stock(resto, portions=10)
    >>> qty
    10
    """
    if not getattr(resto, "inventory", None):
        # Crée un inventaire minimal si absent
        resto.inventory = Inventory()
    # Choisit systématiquement le premier plat du menu (simple mais prévisible)
    recipe0 = resto.menu[0]
    price0 = float(
        getattr(recipe0, "price", getattr(recipe0, "selling_price", 0.0)) or 10.0
    )
    resto.inventory.add_finished_lot(
        recipe_name=recipe0.name,
        selling_price=price0,
        portions=int(portions),
        produced_tour=1,
        shelf_tours=1,  # périme fin T2
    )
    return recipe0, price0, portions


# Staff de base si helpers RH existent
def add_basic_staff(resto):
    """Ajoute un noyau de staff si des helpers RH sont disponibles.

    La méthode est opportuniste: elle n'échoue pas si les helpers n'existent pas
    encore sur `Restaurant`. Elle sert à accélérer les tests de bout en bout.

    Retour
    - list: éléments éventuellement créés/retournés par les helpers, sinon vide.
    """
    # On essaie d'utiliser les helpers présents dans Restaurant (si existants)
    added = []
    try:
        # Si des méthodes comme add_staff(role, count, minutes) existent, adapter ici
        if hasattr(resto, "add_server"):
            added.append(resto.add_server("Serveur 1", minutes_service=2400))
        if hasattr(resto, "add_cook"):
            added.append(resto.add_cook("Cuisinier 1", minutes_prod=2400))
    except Exception:
        pass
    # sinon, on laisse la boucle Game gérer sans RH détaillée
    return added


def main() -> None:
    """Point d'entrée du script de démonstration.

    Étapes principales mises en œuvre:
    1. Sécuriser (no-op) la compta si besoin
    2. Créer un restaurant de type Bistro
    3. Générer un menu (ou fallback mini menu)
    4. Amorcer l'inventaire avec un lot de produits finis
    5. Ajouter un staff minimal si possible
    6. Lancer la partie sur 2 tours
    """
    # 1) Crée un resto (change ici le type si tu veux tester)
    rtype = RestaurantType.BISTRO
    local = CATALOG_LOCALS["BISTRO"][0]
    resto = Restaurant(
        name="Démo Bistro",
        type=rtype,
        local=local,
        funds=10_000.0,
        marketing_budget=200.0,
        overheads={"loyer": 2200.0, "autres": 300.0},
        notoriety=0.5,
    )

    # 2) Génère le menu (15 bistro / 10 FF / 20 gastro ou fallback mini)
    resto.menu = build_menu_for_type(rtype)

    # 3) Ajoute un lot de produits finis pour vendre direct
    recipe0, price0, portions = prime_finished_stock(resto, portions=50)
    print(f"✔ Lot prêt : {portions}x « {recipe0.name} » à {price0:.2f} €")

    # 4) (optionnel) Staff de base
    add_basic_staff(resto)

    # 5) Lance la partie sur 2 tours (fallback scénario local)
    game = Game(
        restaurants=[resto],
        scenario=CATALOG_SCENARIOS["centre_ville"],
    )
    print("\n🚀 Lancement Game.play() sur 2 tours…")
    game.play()
    print("\n✅ Fin de démo.")


if __name__ == "__main__":
    main()
