# -*- coding: utf-8 -*-
"""
Menus simplifiés par type de restaurant.
Construction "lazy" pour éviter les imports circulaires.
"""

def get_default_menus_simple():
    # Imports retardés = pas d’import circulaire au chargement
    from ..domain.restaurant import RestaurantType
    from ..domain.simple_recipe import SimpleRecipe, Technique, Complexity

    return {
        RestaurantType.FAST_FOOD: [
            SimpleRecipe(
                "Burger classique",
                [("Pain burger", 1), ("Steak haché", 1), ("Fromage cheddar", 1)],
                Technique.GRILL,
                Complexity.SIMPLE
            ),
            SimpleRecipe(
                "Frites",
                [("Pommes de terre", 3), ("Huile de friture", 1)],
                Technique.FRITURE,
                Complexity.SIMPLE
            ),
            SimpleRecipe(
                "Wrap poulet",
                [("Tortilla", 1), ("Poulet", 1), ("Salade", 1)],
                Technique.FROID,
                Complexity.SIMPLE
            ),
        ],
        RestaurantType.BISTRO: [
            SimpleRecipe(
                "Salade César",
                [("Laitue", 1), ("Poulet", 1), ("Parmesan", 1)],
                Technique.FROID,
                Complexity.SIMPLE
            ),
            SimpleRecipe(
                "Steak frites",
                [("Steak", 1), ("Pommes de terre", 3), ("Huile de friture", 1)],
                Technique.GRILL,
                Complexity.SIMPLE
            ),
            SimpleRecipe(
                "Quiche lorraine",
                [("Pâte brisée", 1), ("Lardons", 1), ("Œufs", 2), ("Crème", 1)],
                Technique.FOUR,
                Complexity.SIMPLE
            ),
        ],
        RestaurantType.GASTRO: [
            SimpleRecipe(
                "Filet de bœuf Rossini",
                [("Filet de bœuf", 1), ("Foie gras", 1), ("Truffe", 1)],
                Technique.GRILL,
                Complexity.COMPLEXE
            ),
            SimpleRecipe(
                "Soufflé au chocolat",
                [("Chocolat", 2), ("Œufs", 3), ("Sucre", 1)],
                Technique.FOUR,
                Complexity.COMPLEXE
            ),
            SimpleRecipe(
                "Homard breton rôti",
                [("Homard", 1), ("Beurre", 1), ("Herbes fines", 1)],
                Technique.FOUR,
                Complexity.COMPLEXE
            ),
        ]
    }
    # Note: Les recettes sont simplifiées pour l'exemple.