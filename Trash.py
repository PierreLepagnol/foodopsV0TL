# def _run_safe():
#     # Démo ultra-simple en cas d'import cassé : pas de compta, pas d'inventaire,
#     # juste un resto, un menu auto, 3 tours, CA = clients * prix médian.
#     print("⚠️  Mode SAFE : certains imports ont échoué, on lance une démo simplifiée.")

#     import numpy as np

#     local = SimpleNamespace(visibility=4, seats=30)

#     r = Restaurant(
#         name="Demo SAFE",
#         type=RestaurantType.FAST_FOOD,
#         local=local,
#         funds=10000.0,
#     )

#     # tente une génération de menu; sinon plat trivial
#     try:
#         r.menu = build_menu_for_type(r.type)
#     except Exception:
#         r.menu = [
#             SimpleRecipe(
#                 name="Burger test",
#                 price=9.5,
#                 selling_price=9.5,
#                 technique=Technique.GRILLE,
#                 complexity=Complexity.SIMPLE,
#                 base_quality=0.7,
#             ),
#         ]

#     menu = r.menu if hasattr(r, "menu") else []
#     prix_des_items = [item.price for item in menu if item is not None]
#     price = np.median(prix_des_items) if prix_des_items else 0.0

#     print(f"Menu prêt ({len(r.menu)} items). Prix médian: {price:.2f} €")

#     demand_per_tour = 120  # fixe pour la démo
#     capacity = 100  # capacité fixe safe
#     for t in range(1, 4):
#         clients = min(demand_per_tour, capacity)
#         ca = round(clients * price, 2)
#         print(f"T{t}: clients={clients}  CA={ca:.2f} €")

#     print("✅ SAFE demo terminée.")


