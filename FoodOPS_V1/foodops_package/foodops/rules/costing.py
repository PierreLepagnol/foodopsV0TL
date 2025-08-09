# -*- coding: utf-8 -*-
"""
Calculs de coûts matière (COGS) basés sur le référentiel d'ingrédients.
Importe les prix via getter pour éviter les imports circulaires.
"""

from typing import Iterable, Dict
from ..data import get_INGREDIENT_PRICES


def compute_recipe_cogs(recipe) -> float:
    """
    Calcule le coût matière d'une recette (somme prix_unitaire * quantité).
    La recette doit exposer `recipe.ingredients` sous forme [(nom, qty), ...].
    """
    prices = get_INGREDIENT_PRICES()
    total = 0.0
    for name, qty in getattr(recipe, "ingredients", []):
        unit_price = float(prices.get(name, 0.0))
        total += unit_price * float(qty)
    return round(total, 2)


def compute_menu_cogs(menu: Iterable) -> Dict[str, float]:
    """
    Retourne {nom_recette: cogs} pour un menu (liste de recettes).
    """
    out: Dict[str, float] = {}
    for i, r in enumerate(menu):
        key = getattr(r, "name", f"recette_{i}")
        out[key] = compute_recipe_cogs(r)
    return out


def compute_average_unit_cogs(menu: Iterable) -> float:
    """
    Coût matière unitaire moyen d'un menu (moyenne des COGS recettes).
    Utile quand on ne choisit pas la recette précise du client.
    """
    menu = list(menu or [])
    if not menu:
        return 0.0
    values = [compute_recipe_cogs(r) for r in menu]
    return round(sum(values) / len(values), 2)

# --- Pricing policies ---------------------------------------------------------
from enum import Enum

class PricePolicy(Enum):
    """Stratégies de tarification utilisables par les recettes/menus."""
    MARKUP = "markup"            # prix = COGS * (1 + x)        ; x = taux marge brute
    TARGET_MARGIN = "target_margin"  # même chose que MARKUP (alias pédagogique)
    ABSOLUTE = "absolute"        # prix = valeur absolue fournie

def suggest_price_from_cogs(cogs: float, policy: "PricePolicy", value: float) -> float:
    """
    Calcule un prix conseillé en fonction du COGS et d'une politique.
    - MARKUP / TARGET_MARGIN : value = taux de marge brute (ex: 0.7 => 70%)
      prix = cogs * (1 + value)
    - ABSOLUTE : value = prix souhaité
    """
    cogs = float(max(0.0, cogs))
    if policy in (PricePolicy.MARKUP, PricePolicy.TARGET_MARGIN):
        rate = max(0.0, float(value))
        return round(cogs * (1.0 + rate), 2)
    elif policy == PricePolicy.ABSOLUTE:
        return round(max(float(value), 0.0), 2)
    # fallback
    return round(cogs, 2)
