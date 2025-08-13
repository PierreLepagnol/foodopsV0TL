# scripts/smoke_run.py
"""
Test rapide : instancie 1 resto de chaque type, seed l'inventaire, produit et vend, affiche les résultats sur 2 tours.
"""

from FoodOPS_V1.domain.restaurant import Restaurant
from FoodOPS_V1.domain.types import RestaurantType
from FoodOPS_V1.domain.staff import Employe, Role
from FoodOPS_V1.domain.inventory import Inventory, FoodGrade
from FoodOPS_V1.domain.recipe import SimpleRecipe

# Création de 3 restaurants
restos = [
    Restaurant(name="FastFoodTest", type=None, local=None),
    Restaurant(name="BistroTest", type=None, local=None),
    Restaurant(name="GastroTest", type=None, local=None),
]
# Attribution du type

restos[0].type = RestaurantType.FAST_FOOD
restos[1].type = RestaurantType.BISTRO
restos[2].type = RestaurantType.GASTRO

# Ajout d'employés
for r in restos:
    r.equipe = [
        Employe(nom="Alice", role=Role.CUISINIER, salaire_total=2000),
        Employe(nom="Bob", role=Role.SERVEUR, salaire_total=1800),
        Employe(nom="Eve", role=Role.MANAGER, salaire_total=2500),
    ]
    r.reset_rh_minutes()
    r.inventory = Inventory()

# Seed ingrédients (2 gammes)
for r in restos:
    r.inventory.add_ingredient(
        "poulet",
        FoodGrade.G1_FRAIS_BRUT,
        5.0,
        10.0,
        current_tour=1,
        shelf_tours=2,
    )
    r.inventory.add_ingredient(
        "riz", FoodGrade.G3_SURGELE, 3.0, 2.0, current_tour=1, shelf_tours=2
    )

# Création de 2 recettes simples
rec1 = SimpleRecipe(
    name="Poulet Riz",
    main_ingredient="poulet",
    portion_kg=0.2,
    price=12.0,
    base_quality=0.8,
)
rec2 = SimpleRecipe(
    name="Riz Nature",
    main_ingredient="riz",
    portion_kg=0.15,
    price=7.0,
    base_quality=0.6,
)
for r in restos:
    r.add_recipe_to_menu(rec1)
    r.add_recipe_to_menu(rec2)

# Production de portions
for r in restos:
    needs = r._resolve_recipe_needs(rec1)
    for name, qty in needs:
        r.inventory.consume_ingredient(name, qty * 10, current_tour=1)
    r.inventory.add_finished_lot(
        rec1.name, rec1.price, 10, produced_tour=1, shelf_tours=1
    )
    needs = r._resolve_recipe_needs(rec2)
    for name, qty in needs:
        r.inventory.consume_ingredient(name, qty * 8, current_tour=1)
    r.inventory.add_finished_lot(
        rec2.name, rec2.price, 8, produced_tour=1, shelf_tours=1
    )

# Simule 2 tours avec vente FIFO
for tour in range(1, 3):
    print(f"\n--- Tour {tour} ---")
    for r in restos:
        r.inventory.cleanup_expired(tour)
        sold, ca = r.inventory.sell_from_finished_fifo(5)
        print(f"{r.name}: Vendu {sold} portions, CA = {ca} €")
        print(f"Stock restant: {r.inventory.total_finished_portions()} portions")
