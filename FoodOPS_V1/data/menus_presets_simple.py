"""
Menus par type de restaurant basés sur SimpleRecipe et le catalogue multi-gammes.
"""

from typing import Dict, List
from FoodOPS_V1.domain.restaurant import RestaurantType
from FoodOPS_V1.rules.recipe_factory import build_menu_for_type
from FoodOPS_V1.domain.simple_recipe import SimpleRecipe, Technique, Complexity
from FoodOPS_V1.domain.ingredients import Ingredient, CATALOG
from FoodOPS_V1.rules.costing import recipe_cost_and_price


def get_default_menus_simple() -> Dict[RestaurantType, List[SimpleRecipe]]:
    return {
        RestaurantType.FAST_FOOD: build_menu_for_type(RestaurantType.FAST_FOOD),
        RestaurantType.BISTRO: build_menu_for_type(RestaurantType.BISTRO),
        RestaurantType.GASTRO: build_menu_for_type(RestaurantType.GASTRO),
    }


def _pick(ings: List[Ingredient], name: str, grade=None) -> Ingredient:
    cands = [i for i in ings if i.name == name and (grade is None or i.grade == grade)]
    return cands[0] if cands else None


def get_default_menus_simple() -> Dict[RestaurantType, List[SimpleRecipe]]:
    ings = CATALOG
    menus: Dict[RestaurantType, List[SimpleRecipe]] = {
        RestaurantType.FAST_FOOD: [],
        RestaurantType.BISTRO: [],
        RestaurantType.GASTRO: [],
    }

    # ---------- FAST FOOD ----------
    # Burger boeuf (fraîs) + portion 130g
    beef_fresh = _pick(ings, "Steak haché")  # prendra G1 si présent en premier
    beef_frozen = _pick(
        ings, "Steak haché"
    )  # simple : on garde le premier pour frais, on pourrait raffiner
    # Poulet (tenders / sandwich)
    chicken_frozen = [i for i in ings if i.name == "Poulet"][-1]

    r1 = SimpleRecipe.from_ingredient(
        "Burger boeuf", beef_fresh, 0.13, Technique.GRILLE, Complexity.SIMPLE
    )
    r2 = SimpleRecipe.from_ingredient(
        "Tenders de poulet",
        chicken_frozen,
        0.15,
        Technique.FRIT,
        Complexity.SIMPLE,
    )
    r3 = SimpleRecipe.from_ingredient(
        "Salade oeufs",
        _pick(ings, "oeufs"),
        0.06,
        Technique.FROID,
        Complexity.SIMPLE,
    )

    # ---------- BISTRO ----------
    cod_fresh = [i for i in ings if i.name == "Cabillaud" and "FRAIS" in i.grade.name][
        0
    ]
    r4 = SimpleRecipe.from_ingredient(
        "Cabillaud rôti", cod_fresh, 0.16, Technique.ROTI, Complexity.SIMPLE
    )
    r5 = SimpleRecipe.from_ingredient(
        "Poulet sauté",
        _pick(ings, "Poulet"),
        0.18,
        Technique.SAUTE,
        Complexity.SIMPLE,
    )

    # ---------- GASTRO ----------
    salmon_fresh = [i for i in ings if i.name == "Saumon" and "FRAIS" in i.grade.name][
        0
    ]
    r6 = SimpleRecipe.from_ingredient(
        "Saumon mi-cuit",
        salmon_fresh,
        0.16,
        Technique.ROTI,
        Complexity.COMPLEXE,
    )
    r7 = SimpleRecipe.from_ingredient(
        "oeuf parfait",
        _pick(ings, "oeufs"),
        0.05,
        Technique.VAPEUR,
        Complexity.COMPLEXE,
    )

    # Prix conseillés selon politique FC%
    for r in [r1, r2, r3]:
        c, p = recipe_cost_and_price(RestaurantType.FAST_FOOD, r)
        r.selling_price = p  # on stocke le prix conseillé directement

    for r in [r4, r5]:
        c, p = recipe_cost_and_price(RestaurantType.BISTRO, r)
        r.selling_price = p

    for r in [r6, r7]:
        c, p = recipe_cost_and_price(RestaurantType.GASTRO, r)
        r.selling_price = p

    menus[RestaurantType.FAST_FOOD] = [r1, r2, r3]
    menus[RestaurantType.BISTRO] = [r4, r5]
    menus[RestaurantType.GASTRO] = [r6, r7]

    return menus
