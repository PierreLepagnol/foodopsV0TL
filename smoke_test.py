# scripts/smoke_test.py
"""
Smoke test minimal — ne dépend pas de la compta.
Valide :
- création d'un resto (Bistrot par défaut),
- génération d'un menu auto (15 plats),
- ajout d'un lot de produits finis,
- vente FIFO de X couverts,
- affichage des chiffres de base (CA, COGS reconnu si utilisé).
"""

from types import SimpleNamespace

# Imports robustes (adapte "foodops" si ton package s'appelle autrement)
from FoodOPS_V1.domain.restaurant import Restaurant, RestaurantType
from FoodOPS_V1.domain.inventory import Inventory
from FoodOPS_V1.rules.recipe_factory import build_menu_for_type


# Petit local factice
class LocalStub:
    def __init__(self, visibility=3.0, seats=40):
        self.visibility = visibility
        self.seats = seats


def fmt(x):  # euros
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def main():
    # 1) Resto bistro (mais tu peux passer FAST_FOOD / GASTRO)
    rtype = RestaurantType.BISTRO
    resto = Restaurant(
        name="SmokeTest Bistro",
        type=rtype,
        local=LocalStub(visibility=3.5, seats=42),
    )

    # 2) Menu auto (15 recettes pour un bistro)
    menu = build_menu_for_type(rtype)
    resto.menu = menu
    print(f"✔ Menu généré : {len(menu)} recettes. Exemple :")
    for m in menu[:3]:
        price = getattr(m, "price", getattr(m, "selling_price", 0.0))
        print(f"   - {m.name} — {fmt(price)} (q≈{getattr(m, 'base_quality', 0.0):.2f})")

    # 3) Injecte un lot de produits finis (simulateur de prod)
    resto.inventory = Inventory()
    recipe0 = menu[0]
    price0 = float(
        getattr(recipe0, "price", getattr(recipe0, "selling_price", 0.0)) or 10.0
    )
    portions = 30
    resto.inventory.add_finished_lot(
        recipe_name=recipe0.name,
        selling_price=price0,
        portions=portions,
        produced_tour=1,  # vendable T1, périme fin T2 par défaut
        shelf_tours=1,
    )
    print(f"✔ Lot ajouté: {portions} portions de « {recipe0.name} » à {fmt(price0)}")

    # 4) Vendre 24 couverts (FIFO)
    ask = 24
    sold, revenue = resto.inventory.sell_from_finished_fifo(ask)
    print(f"✔ Vente : demandé={ask}, vendu={sold}, CA={fmt(revenue)}")

    # 5) Montre le stock restant
    left = resto.inventory.total_finished_portions()
    print(f"✔ Restant en produits finis : {left} portions")

    # 6) Mini résumé (sans compta)
    result = SimpleNamespace(
        restaurant_name=resto.name,
        clients_serv=sold,
        ca=revenue,
        remaining_portions=left,
        menu_size=len(menu),
        first_dish=recipe0.name,
        first_dish_price=price0,
    )
    print("\n=== Résumé Smoke Test ===")
    print(f"Resto       : {result.restaurant_name}")
    print(f"Menu        : {result.menu_size} recettes")
    print(f"Plat #1     : {result.first_dish} — {fmt(result.first_dish_price)}")
    print(f"Servis      : {result.clients_serv}")
    print(f"Chiffre d'affaires : {fmt(result.ca)}")
    print(f"Reste stock : {result.remaining_portions} portions")
    print("=========================\n")


if __name__ == "__main__":
    main()
