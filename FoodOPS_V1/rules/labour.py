# foodops/rules/labour.py

from FoodOPS_V1.domain.simple_recipe import Technique, Complexity

# minutes/portion (base) par technique
TECH_MIN_PER_PORTION = {
    Technique.FROID: 2.0,
    Technique.GRILLE: 4.0,
    Technique.SAUTE: 5.0,
    Technique.ROTI: 6.0,
    Technique.FRIT: 3.5,
    Technique.VAPEUR: 4.0,
}

# multiplicateur selon complexité
CPLX_MULT = {
    Complexity.SIMPLE: 1.0,
    Complexity.COMPLEXE: 1.3,
}


def recipe_prep_minutes_per_portion(recipe) -> float:
    """Minutes de préparation par portion estimées pour une recette.

    Base dépendant de la `Technique`, multipliée selon la `Complexity`.

    Exemple
    -------
    >>> from FoodOPS_V1.domain.simple_recipe import SimpleRecipe, Technique, Complexity
    >>> r = SimpleRecipe(name="Salade", technique=Technique.FROID, complexity=Complexity.SIMPLE)
    >>> round(recipe_prep_minutes_per_portion(r), 2)
    2.0
    >>> r2 = SimpleRecipe(name="Poêlée", technique=Technique.SAUTE, complexity=Complexity.COMPLEXE)
    >>> round(recipe_prep_minutes_per_portion(r2), 2)
    6.5
    """
    base = TECH_MIN_PER_PORTION.get(recipe.technique, 4.0)
    mult = CPLX_MULT.get(recipe.complexity, 1.0)
    return base * mult
