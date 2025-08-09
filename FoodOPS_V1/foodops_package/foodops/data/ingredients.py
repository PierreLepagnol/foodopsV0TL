# -*- coding: utf-8 -*-
"""
Shim de compatibilité : ré-exporte le contenu de ingredients_fr
pour les anciens imports `foodops.data.ingredients`.
"""

# Ré-export direct depuis ton module existant
from .ingredients_fr import (
    IngredientCategory,
    FoodGrade,
    Ingredient,
    QUALITY_PERCEPTION,
    get_all_ingredients,
)

__all__ = [
    "IngredientCategory",
    "FoodGrade",
    "Ingredient",
    "QUALITY_PERCEPTION",
    "get_all_ingredients",
]
