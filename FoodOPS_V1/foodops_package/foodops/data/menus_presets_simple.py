# -*- coding: utf-8 -*-
# foodops/data/menus_presets_simple.py  (NOUVELLE VERSION)
from typing import Dict, List
from ..domain.restaurant import RestaurantType
from ..rules.recipes_factory import build_menu_for_type
from ..domain.simple_recipe import SimpleRecipe

def get_default_menus_simple() -> Dict[RestaurantType, List[SimpleRecipe]]:
    return {
        RestaurantType.FAST_FOOD: build_menu_for_type(RestaurantType.FAST_FOOD),
        RestaurantType.BISTRO:    build_menu_for_type(RestaurantType.BISTRO),
        RestaurantType.GASTRO:    build_menu_for_type(RestaurantType.GASTRO),
    }
# -*- coding: utf-8 -*-
"""
Menus par type de restaurant basés sur SimpleRecipe et le catalogue multi-gammes.
"""

from typing import Dict, List
from ..domain import RestaurantType
from ..domain.simple_recipe import SimpleRecipe, Technique, Complexity
from ..data.ingredients import get_all_ingredients, Ingredient
from ..rules.costing import recipe_cost_and_price


def _pick(ings: List[Ingredient], name: str, grade=None) -> Ingredient:
    cands = [i for i in ings if i.name == name and (grade is None or i.grade == grade)]
    return cands[0] if cands else None


def get_default_menus_simple() -> Dict[RestaurantType, List[SimpleRecipe]]:
    ings = get_all_ingredients()
    menus: Dict[RestaurantType, List[SimpleRecipe]] = {
        RestaurantType.FAST_FOOD: [],
        RestaurantType.BISTRO: [],
        RestaurantType.GASTRO: [],
    }

    # ---------- FAST FOOD ----------
    # Burger bœuf (fraîs) + portion 130g
    beef_fresh = _pick(ings, "Steak haché")           # prendra G1 si présent en premier
    beef_frozen = _pick(ings, "Steak haché")          # simple : on garde le premier pour frais, on pourrait raffiner
    # Poulet (tenders / sandwich)
    chicken_frozen = [i for i in ings if i.name == "Poulet"][-1]

    r1 = SimpleRecipe.from_ingredient("Burger bœuf", beef_fresh, 0.13, Technique.GRILLE, Complexity.SIMPLE)
    r2 = SimpleRecipe.from_ingredient("Tenders de poulet", chicken_frozen, 0.15, Technique.FRIT, Complexity.SIMPLE)
    r3 = SimpleRecipe.from_ingredient("Salade œufs", _pick(ings, "Œufs"), 0.06, Technique.FROID, Complexity.SIMPLE)

    # ---------- BISTRO ----------
    cod_fresh = [i for i in ings if i.name == "Cabillaud" and "FRAIS" in i.grade.name][0]
    r4 = SimpleRecipe.from_ingredient("Cabillaud rôti", cod_fresh, 0.16, Technique.ROTI, Complexity.SIMPLE)
    r5 = SimpleRecipe.from_ingredient("Poulet sauté", _pick(ings, "Poulet"), 0.18, Technique.SAUTE, Complexity.SIMPLE)

    # ---------- GASTRO ----------
    salmon_fresh = [i for i in ings if i.name == "Saumon" and "FRAIS" in i.grade.name][0]
    r6 = SimpleRecipe.from_ingredient("Saumon mi-cuit", salmon_fresh, 0.16, Technique.ROTI, Complexity.COMPLEXE)
    r7 = SimpleRecipe.from_ingredient("Œuf parfait", _pick(ings, "Œufs"), 0.05, Technique.VAPEUR, Complexity.COMPLEXE)

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
    menus[RestaurantType.BISTRO]    = [r4, r5]
    menus[RestaurantType.GASTRO]    = [r6, r7]

    return menus