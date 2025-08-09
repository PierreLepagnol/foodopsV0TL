# -*- coding: utf-8 -*-
"""
Lanceur 'python -m foodops'

- Mode NORMAL : tente d'exécuter le vrai Game si tout est en place.
- Mode SAFE   : si un import casse, on lance une démo minimaliste (1 resto, 3 tours)
                sans dépendances lourdes (compta, RH, inventaire…). Objectif :
                vérifier que le package est exécutable, que les menus se génèrent,
                et que le scoring/prix fonctionne basique.
"""

import sys
from types import SimpleNamespace

def _run_normal():
    # Essaie la boucle complète si elle est dispo
    from foodops.core.game import Game  # ton vrai moteur
    from foodops.domain.restaurant import Restaurant, RestaurantType
    # petit local de test
    local = SimpleNamespace(visibility=4, seats=30)
    r = Restaurant(
        name="Demo Resto",
        type=RestaurantType.BISTRO,
        local=local,
        funds=20000.0,
        overheads={"loyer": 2000.0, "autres": 500.0},
        marketing_budget=300.0,
    )

    # Si tu as une factory de menus auto :
    try:
        from foodops.rules.recipes_factory import build_menu_for_type
        r.menu = build_menu_for_type(r.type)
    except Exception:
        # fallback : menu trivial
        from foodops.domain.simple_recipe import SimpleRecipe, Technique, Complexity
        r.menu = [
            SimpleRecipe(name="Plat du jour", price=15.0, selling_price=15.0,
                         technique=Technique.GRILLE, complexity=Complexity.SIMPLE, base_quality=0.8),
        ]

    # Scenario par défaut si dispo
    scenario = None
    try:
        from foodops.data.scenario_presets import get_default_scenario
        scenario = get_default_scenario()
    except Exception:
        pass

    game = Game(restaurants=[r], scenario=scenario)
    game.play()

def _run_safe():
    # Démo ultra-simple en cas d'import cassé : pas de compta, pas d'inventaire,
    # juste un resto, un menu auto, 3 tours, CA = clients * prix médian.
    print("⚠️  Mode SAFE : certains imports ont échoué, on lance une démo simplifiée.")
    from foodops.domain.restaurant import Restaurant, RestaurantType
    from foodops.rules.scoring import menu_price_median
    local = SimpleNamespace(visibility=4, seats=30)

    r = Restaurant(
        name="Demo SAFE",
        type=RestaurantType.FAST_FOOD,
        local=local,
        funds=10000.0,
    )

    # tente une génération de menu; sinon plat trivial
    try:
        from foodops.rules.recipes_factory import build_menu_for_type
        r.menu = build_menu_for_type(r.type)
    except Exception:
        from foodops.domain.simple_recipe import SimpleRecipe, Technique, Complexity
        r.menu = [
            SimpleRecipe(name="Burger test", price=9.5, selling_price=9.5,
                         technique=Technique.GRILLE, complexity=Complexity.SIMPLE, base_quality=0.7),
        ]

    price = menu_price_median(r)
    print(f"Menu prêt ({len(r.menu)} items). Prix médian: {price:.2f} €")

    demand_per_tour = 120  # fixe pour la démo
    capacity = 100         # capacité fixe safe
    for t in range(1, 4):
        clients = min(demand_per_tour, capacity)
        ca = round(clients * price, 2)
        print(f"T{t}: clients={clients}  CA={ca:.2f} €")

    print("✅ SAFE demo terminée.")

if __name__ == "__main__":
    try:
        _run_normal()
    except Exception as e:
        # Affiche l’erreur pour info, puis bascule en SAFE
        print("❌ Mode NORMAL indisponible :", repr(e))
        try:
            _run_safe()
        except Exception as e2:
            print("🔥 Même le mode SAFE a échoué :", repr(e2))
            sys.exit(1)
