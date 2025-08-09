# -*- coding: utf-8 -*-
# scripts/run_full_demo.py
"""
Demo complète et robuste :
- crée 1 restaurant (type au choix),
- génère un menu (recipes_factory) ou mini menu fallback,
- injecte un lot de produits finis,
- ajoute un peu de staff (si helpers présents),
- lance Game.play() sur 2 tours,
- affiche les résultats.

Le script est tolérant : si la compta ou le scénario natif n’existent pas,
il passe en fallback (no-op compta, scénario local simple).
"""

from types import SimpleNamespace
import sys

# ---- Imports robustes -------------------------------------------------------
try:
    from FoodOPS_V1.foodops_package.foodops.core.game import Game
except Exception as e:
    print("❌ Impossible d’importer Game. Vérifie foodops/core/game.py")
    raise

try:
    from FoodOPS_V1.foodops_package.foodops.domain.restaurant import Restaurant, RestaurantType
except Exception:
    print("❌ Impossible d’importer Restaurant/RestaurantType.")
    raise

# Local “stub” (visibilité, places) pour éviter de dépendre d’un Local réel
class LocalStub:
    def __init__(self, visibility=3.5, seats=45):
        self.visibility = visibility
        self.seats = seats

def build_menu_for(resto_type):
    try:
        from FoodOPS_V1.foodops_package.foodops.rules.recipe_factory import build_menu_for_type
        return build_menu_for_type(resto_type)
    except Exception:
        # Fallback minimal : 2 plats génériques
        from FoodOPS_V1.foodops_package.foodops.domain.simple_recipe import SimpleRecipe
        r1 = SimpleRecipe(name="Plat simple", price=12.0, selling_price=12.0, base_quality=0.7)
        r2 = SimpleRecipe(name="Plat combo", price=15.0, selling_price=15.0, base_quality=0.75)
        return [r1, r2]

# Injecte un lot de produits finis pour pouvoir vendre au tour 1
def prime_finished_stock(resto, portions=40):
    try:
        from FoodOPS_V1.foodops_package.foodops.domain.inventory import Inventory
    except Exception:
        print("❌ Inventory introuvable (foodops/domain/inventory.py).")
        raise
    if not getattr(resto, "inventory", None):
        resto.inventory = Inventory()
    # choisit le premier plat du menu
    recipe0 = resto.menu[0]
    price0 = float(getattr(recipe0, "price", getattr(recipe0, "selling_price", 0.0)) or 10.0)
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
    # On essaie d’utiliser les helpers présents dans Restaurant (si existants)
    added = []
    try:
        # Si tu as des méthodes comme add_staff(role, count, minutes), adapte ici.
        if hasattr(resto, "add_server"):
            added.append(resto.add_server("Serveur 1", minutes_service=2400))
        if hasattr(resto, "add_cook"):
            added.append(resto.add_cook("Cuisinier 1", minutes_prod=2400))
    except Exception:
        pass
    # sinon, on laisse la boucle Game gérer sans RH détaillée
    return added

# Comptabilité no-op si nécessaire
def ensure_accounting_noop():
    try:
        from FoodOPS_V1.foodops_package.foodops.core import accounting as acc
        # on teste l’existence des fonctions ; si elles n’existent pas, on no-op
        needed = ["post_sales", "post_cogs", "post_services_ext", "post_payroll",
                  "post_depreciation", "post_loan_payment", "month_amortization"]
        for fn in needed:
            if not hasattr(acc, fn):
                raise RuntimeError("missing acc fn")
        return  # tout va bien
    except Exception:
        # Monkeypatch no-op minimal
        print("⚠️  Comptabilité indisponible : passage en no-op.")
        import types
        noop_mod = types.SimpleNamespace(
            post_sales=lambda *a, **k: None,
            post_cogs=lambda *a, **k: None,
            post_services_ext=lambda *a, **k: None,
            post_payroll=lambda *a, **k: None,
            post_depreciation=lambda *a, **k: None,
            post_loan_payment=lambda *a, **k: None,
            month_amortization=lambda *a, **k: 0.0,
        )
        sys.modules['FoodOPS_V1.foodops_package.foodops.core.accounting'] = noop_mod

def main():
    ensure_accounting_noop()

    # 1) Crée un resto (change ici le type si tu veux tester)
    rtype = RestaurantType.BISTRO
    resto = Restaurant(
        name="Démo Bistro",
        type=rtype,
        local=LocalStub(visibility=3.8, seats=44),
        funds=10_000.0,
        marketing_budget=200.0,
        overheads={"loyer": 2200.0, "autres": 300.0},
        notoriety=0.5,
    )

    # 2) Génère le menu (15 bistro / 10 FF / 20 gastro ou fallback mini)
    resto.menu = build_menu_for(rtype)

    # 3) Ajoute un lot de produits finis pour vendre direct
    recipe0, price0, portions = prime_finished_stock(resto, portions=50)
    print(f"✔ Lot prêt : {portions}x « {recipe0.name} » à {price0:.2f} €")

    # 4) (optionnel) Staff de base
    add_basic_staff(resto)

    # 5) Lance la partie sur 2 tours (fallback scénario local)
    game = Game(restaurants=[resto], scenario=SimpleNamespace(nb_tours=2, demand_per_tour=600))
    print("\n🚀 Lancement Game.play() sur 2 tours…")
    game.play()
    print("\n✅ Fin de démo.")

if __name__ == "__main__":
    main()
