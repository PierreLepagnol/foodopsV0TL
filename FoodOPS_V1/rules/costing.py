"""
Coûts recettes (COGS) + politiques de prix conseillés.
"""

from enum import Enum, auto
from typing import Tuple
from FoodOPS_V1.domain import RestaurantType
from FoodOPS_V1.domain.simple_recipe import SimpleRecipe, Technique, Complexity
from FoodOPS_V1.domain.ingredients import FoodGrade


# Multiplicateurs matière (€/kg effectif) par gamme
GRADE_COST_MULT = {
    FoodGrade.G1_FRAIS_BRUT: 1.00,
    FoodGrade.G2_CONSERVE: 0.95,
    FoodGrade.G3_SURGELE: 0.92,
    FoodGrade.G4_CRU_PRET: 1.08,  # prêt à l'emploi souvent plus cher/kg net
    FoodGrade.G5_CUIT_SOUS_VIDE: 1.12,
}

# Coût “main d'oeuvre + énergie + consommables” par portion (euros)
# (modèle simple, on affinera plus tard via RH réels)
LABOUR_ENERGY_PER_PORTION_BASE = 0.40
TECH_FACTOR = {
    Technique.FROID: 0.8,
    Technique.GRILLE: 1.1,
    Technique.SAUTE: 1.0,
    Technique.ROTI: 1.1,
    Technique.FRIT: 1.15,
    Technique.VAPEUR: 0.9,
}
CPLX_FACTOR = {
    Complexity.SIMPLE: 1.0,
    Complexity.COMPLEXE: 1.25,
}


def compute_recipe_cogs(r: SimpleRecipe) -> float:
    """Calcule le COGS (€/portion) d'une recette simple.

    Combine un coût matière (prix/kg x portion x multiplicateur de gamme)
    et un forfait main d'oeuvre/énergie modulé par technique et complexité.

    Formule
    -------
    COGS = mat_cost + mo_cost

    Où:
    - ing_price = base_price_per_kg x GRADE_COST_MULT[grade]
    - mat_cost = ing_price x portion_kg
    - mo_cost = LABOUR_ENERGY_PER_PORTION_BASE x TECH_FACTOR[technique] x CPLX_FACTOR[complexity]

    Détails des multiplicateurs:
    - GRADE_COST_MULT: G1_FRAIS_BRUT=1.00, G2_CONSERVE=0.95, G3_SURGELE=0.92, G4_CRU_PRET=1.08, G5_CUIT_SOUS_VIDE=1.12
    - LABOUR_ENERGY_PER_PORTION_BASE = 0.40€
    - TECH_FACTOR: FROID=0.8, GRILLE=1.1, SAUTE=1.0, ROTI=1.1, FRIT=1.15, VAPEUR=0.9
    - CPLX_FACTOR: SIMPLE=1.0, COMPLEXE=1.25

    """
    ingredient_unit_price = (
        r.main_ingredient.base_priceformat_currency_eur_per_kg
        * GRADE_COST_MULT.get(r.grade, 1.0)
    )
    mat_cost = ingredient_unit_price * r.portion_kg
    mo_cost = (
        LABOUR_ENERGY_PER_PORTION_BASE
        * TECH_FACTOR.get(r.technique, 1.0)
        * CPLX_FACTOR.get(r.complexity, 1.0)
    )
    return round(mat_cost + mo_cost, 2)


class PricePolicy(Enum):
    FOOD_COST_TARGET = auto()  # prix conseillé en visant % matière cible
    MARGIN_PER_PORTION = auto()  # prix conseillé avec marge € cible


FOOD_COST_TARGET = {
    RestaurantType.FAST_FOOD: 0.30,
    RestaurantType.BISTRO: 0.28,
    RestaurantType.GASTRO: 0.25,
}

DEFAULT_MARGIN_PER_PORTION = {
    RestaurantType.FAST_FOOD: 2.5,
    RestaurantType.BISTRO: 4.0,
    RestaurantType.GASTRO: 7.0,
}


def suggest_price(
    rtype: RestaurantType,
    recipe: SimpleRecipe,
    policy: PricePolicy = PricePolicy.FOOD_COST_TARGET,
) -> float:
    """Propose un prix de vente selon une politique donnée.

    Formules
    --------
    Politique FOOD_COST_TARGET (par défaut):
        price = COGS / food_cost_target_percentage

    Politique MARGIN_PER_PORTION:
        price = COGS + fixed_margin_per_portion

    Paramètres par type de restaurant:
    - FOOD_COST_TARGET: FAST_FOOD=30%, BISTRO=28%, GASTRO=25%
    - DEFAULT_MARGIN_PER_PORTION: FAST_FOOD=2.5€, BISTRO=4.0€, GASTRO=7.0€

    Note: Le food_cost_target est plafonné à minimum 5% pour éviter les divisions par zéro.

    Exemple
    -------
    >>> from FoodOPS_V1.domain import RestaurantType
    >>> from FoodOPS_V1.domain.simple_recipe import SimpleRecipe, Technique, Complexity
    >>> from FoodOPS_V1.domain.ingredients import Ingredient, IngredientCategory, FoodGrade
    >>> ing = Ingredient(
    ...     name="Poulet", base_priceformat_currency_eur_per_kg=7.5,
    ...     category=IngredientCategory.VIANDE, grade=FoodGrade.G1_FRAIS_BRUT, perish_days=5
    ... )
    >>> r = SimpleRecipe(
    ...     name="Poulet poêlé", main_ingredient=ing, portion_kg=0.15,
    ...     technique=Technique.SAUTE, complexity=Complexity.SIMPLE
    ... )
    >>> r.grade = FoodGrade.G1_FRAIS_BRUT
    >>> suggest_price(RestaurantType.BISTRO, r)
    5.46
    >>> suggest_price(RestaurantType.BISTRO, r, PricePolicy.MARGIN_PER_PORTION)
    5.53
    """
    cogs = compute_recipe_cogs(recipe)
    if policy == PricePolicy.MARGIN_PER_PORTION:
        margin = DEFAULT_MARGIN_PER_PORTION.get(rtype, 3.0)
        return round(cogs + margin, 2)
    # par défaut : % coût matière cible
    fc = FOOD_COST_TARGET.get(rtype, 0.30)
    price = cogs / max(0.05, fc)
    return round(price, 2)


def recipe_cost_and_price(
    restaurant_type: RestaurantType, recipe: SimpleRecipe
) -> Tuple[float, float]:
    """Renvoie le couple (COGS, prix_conseillé).

    Formule
    -------
    result = (compute_recipe_cogs(recipe), suggest_price(rtype, recipe, FOOD_COST_TARGET))

    Cette fonction combine:
    1. compute_recipe_cogs() pour calculer le coût de revient
    2. suggest_price() avec la politique FOOD_COST_TARGET par défaut

    Retourne un tuple (COGS_en_euros, prix_suggéré_en_euros)

    Exemple
    -------
    >>> from FoodOPS_V1.domain import RestaurantType
    >>> from FoodOPS_V1.domain.simple_recipe import SimpleRecipe, Technique, Complexity
    >>> from FoodOPS_V1.domain.ingredients import Ingredient, IngredientCategory, FoodGrade
    >>> ing = Ingredient(
    ...     name="Poulet", base_priceformat_currency_eur_per_kg=7.5,
    ...     category=IngredientCategory.VIANDE, grade=FoodGrade.G1_FRAIS_BRUT, perish_days=5
    ... )
    >>> rec = SimpleRecipe(
    ...     name="Poulet poêlé", main_ingredient=ing, portion_kg=0.15,
    ...     technique=Technique.SAUTE, complexity=Complexity.SIMPLE
    ... )
    >>> rec.grade = FoodGrade.G1_FRAIS_BRUT
    >>> recipe_cost_and_price(RestaurantType.BISTRO, rec)
    (1.53, 5.46)
    """
    c = compute_recipe_cogs(recipe)
    p = suggest_price(restaurant_type, recipe, PricePolicy.FOOD_COST_TARGET)
    return (c, p)
