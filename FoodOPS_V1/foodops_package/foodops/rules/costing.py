# -*- coding: utf-8 -*-
"""
Coûts recettes (COGS) + politiques de prix conseillés.
Importe les enums depuis la recette (pas l'inverse) pour éviter les cycles.
"""

from enum import Enum, auto
from typing import Tuple
from ..domain import RestaurantType
from ..domain.simple_recipe import SimpleRecipe, Technique, Complexity
from ..data.ingredients import FoodGrade


# Multiplicateurs matière (€/kg effectif) par gamme
GRADE_COST_MULT = {
    FoodGrade.G1_FRAIS_BRUT:     1.00,
    FoodGrade.G2_CONSERVE:       0.95,
    FoodGrade.G3_SURGELE:        0.92,
    FoodGrade.G4_CRU_PRET:       1.08,  # prêt à l'emploi souvent plus cher/kg net
    FoodGrade.G5_CUIT_SOUS_VIDE: 1.12,
}

# Coût “main d’œuvre + énergie + consommables” par portion (euros)
# (modèle simple, on affinera plus tard via RH réels)
LABOUR_ENERGY_PER_PORTION_BASE = 0.40
TECH_FACTOR = {
    Technique.FROID:  0.8,
    Technique.GRILLE: 1.1,
    Technique.SAUTE:  1.0,
    Technique.ROTI:   1.1,
    Technique.FRIT:   1.15,
    Technique.VAPEUR: 0.9,
}
CPLX_FACTOR = {
    Complexity.SIMPLE:   1.0,
    Complexity.COMPLEXE: 1.25,
}


def compute_recipe_cogs(r: SimpleRecipe) -> float:
    """Coût matière + petit forfait MO/énergie/consommables (€/portion)."""
    ing_price = r.main_ingredient.base_price_eur_per_kg * GRADE_COST_MULT.get(r.grade, 1.0)
    mat_cost = ing_price * r.portion_kg
    mo_cost = LABOUR_ENERGY_PER_PORTION_BASE * TECH_FACTOR.get(r.technique, 1.0) * CPLX_FACTOR.get(r.complexity, 1.0)
    return round(mat_cost + mo_cost, 2)


class PricePolicy(Enum):
    FOOD_COST_TARGET = auto()  # prix conseillé en visant % matière cible
    MARGIN_PER_PORTION = auto()  # prix conseillé avec marge € cible


FOOD_COST_TARGET = {
    RestaurantType.FAST_FOOD: 0.30,
    RestaurantType.BISTRO:    0.28,
    RestaurantType.GASTRO:    0.25,
}

DEFAULT_MARGIN_PER_PORTION = {
    RestaurantType.FAST_FOOD: 2.5,
    RestaurantType.BISTRO:    4.0,
    RestaurantType.GASTRO:    7.0,
}


def suggest_price(rtype: RestaurantType, recipe: SimpleRecipe,
                  policy: PricePolicy = PricePolicy.FOOD_COST_TARGET) -> float:
    cogs = compute_recipe_cogs(recipe)
    if policy == PricePolicy.MARGIN_PER_PORTION:
        margin = DEFAULT_MARGIN_PER_PORTION.get(rtype, 3.0)
        return round(cogs + margin, 2)
    # par défaut : % coût matière cible
    fc = FOOD_COST_TARGET.get(rtype, 0.30)
    price = cogs / max(0.05, fc)
    return round(price, 2)


def recipe_cost_and_price(rtype: RestaurantType, recipe: SimpleRecipe) -> Tuple[float, float]:
    """Renvoie (cogs, prix_conseillé)."""
    c = compute_recipe_cogs(recipe)
    p = suggest_price(rtype, recipe, PricePolicy.FOOD_COST_TARGET)
    return (c, p)
