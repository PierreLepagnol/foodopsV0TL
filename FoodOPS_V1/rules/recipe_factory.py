"""Génération de recettes et de menus à partir du catalogue d'ingrédients.

Ce module fournit des utilitaires pour:
- déterminer les combinaisons d'ingrédients compatibles selon leurs catégories,
- choisir une technique culinaire adaptée à la catégorie principale,
- estimer des coûts matières par portion et un prix de vente indicatif selon le type de restaurant,
- générer des recettes simples et des *combos* (association de deux ingrédients),
- construire un menu varié pour un type de restaurant donné.

Les fonctions internes (préfixées par « _ ») sont conçues pour être testables
individuellement et réutilisées par la fonction publique `build_menu_for_type`.
Les docstrings incluent des exemples doctest pour faciliter la validation rapide.
"""

from typing import List, Tuple, Dict
import random

from FoodOPS_V1.domain.simple_recipe import SimpleRecipe, Technique, Complexity
from FoodOPS_V1.domain.restaurant import RestaurantType
from FoodOPS_V1.domain.ingredients import (
    IngredientCategory,
    FoodGrade,
    Ingredient,
    CATALOG,
)

# ---------------- Compatibilités & styles ----------------

_ALLOWED_COMBOS: Tuple[Tuple[IngredientCategory, IngredientCategory], ...] = (
    (IngredientCategory.VIANDE, IngredientCategory.LEGUME),
    (IngredientCategory.VIANDE, IngredientCategory.FECULENT),
    (IngredientCategory.POISSON, IngredientCategory.LEGUME),
    (IngredientCategory.POISSON, IngredientCategory.FECULENT),
)

_TECH_BY_CAT = {
    IngredientCategory.VIANDE: [Technique.GRILLE, Technique.SAUTE],
    IngredientCategory.POISSON: [
        Technique.FOUR,
        Technique.SAUTE,
        Technique.FROID,
    ],
    IngredientCategory.LEGUME: [
        Technique.FOUR,
        Technique.SAUTE,
        Technique.FROID,
    ],
    IngredientCategory.FECULENT: [Technique.FOUR, Technique.SAUTE],
    IngredientCategory.CONDIMENT: [Technique.FROID, Technique.SAUTE],
    IngredientCategory.BOULANGERIE: [Technique.FOUR, Technique.FROID],
    IngredientCategory.PRODUIT_LAITIER: [Technique.FROID, Technique.SAUTE],
}

# marges “type” pour prix de vente
MARGIN_BY_RESTO = {
    RestaurantType.FAST_FOOD: 2.5,
    RestaurantType.BISTRO: 3.0,
    RestaurantType.GASTRO: 3.8,
}

# portions (kg) indicatives par catégorie (pour 1 portion)
PORTION_KG = {
    IngredientCategory.VIANDE: 0.15,
    IngredientCategory.POISSON: 0.12,
    IngredientCategory.LEGUME: 0.10,
    IngredientCategory.FECULENT: 0.08,
    IngredientCategory.PRODUIT_LAITIER: 0.05,
    IngredientCategory.BOULANGERIE: 0.08,
    IngredientCategory.CONDIMENT: 0.01,
}


def _allowed_for_type(item: Ingredient, rtype: RestaurantType) -> bool:
    """Vérifie si un item du catalogue est accessible au type de restaurant.

    Paramètres
    ----------
    item : Ingredient
        L'élément du catalogue à tester (contient la clé `tier`).
    rtype : RestaurantType
        Type de restaurant pour lequel on teste l'éligibilité.

    Retour
    ------
    bool
        ``True`` si l'ingrédient est disponible pour ce type de restaurant.

    Notes
    -----
    La logique s'appuie sur `item.tier`:
    - ``ALL``: disponible partout
    - ``BISTRO+``: disponible en ``BISTRO`` et ``GASTRO``
    - ``GASTRO_ONLY``: uniquement en ``GASTRO``

    Exemple
    -------
    >>> from FoodOPS_V1.domain.ingredients import CATALOG
    >>> from FoodOPS_V1.domain.restaurant import RestaurantType
    >>> it = CATALOG["Homard"]
    >>> _allowed_for_type(it, RestaurantType.GASTRO)
    True
    >>> _allowed_for_type(it, RestaurantType.BISTRO)
    False
    """
    if item.tier == "ALL":
        return True
    if item.tier == "BISTRO+" and rtype in (
        RestaurantType.BISTRO,
        RestaurantType.GASTRO,
    ):
        return True
    if item.tier == "GASTRO_ONLY" and rtype == RestaurantType.GASTRO:
        return True
    return False


def _name_simple(ing_name: str, tech: Technique, rtype: RestaurantType) -> str:
    """Construit un nom de recette simple adapté au concept.

    Paramètres
    ----------
    ing_name : str
        Nom de l'ingrédient principal.
    tech : Technique
        Technique culinaire retenue.
    rtype : RestaurantType
        Type de restaurant (influence certains intitulés).

    Retour
    ------
    str
        Nom lisible de la recette.

    Notes
    -----
    Cas particuliers pour ``FAST_FOOD`` (ex. burger, fish & chips), sinon
    une formulation générique est utilisée (ex. « rôti », « poêlé »).

    Exemple
    -------
    >>> _name_simple("Poulet", Technique.SAUTE, RestaurantType.FAST_FOOD)
    'Burger de poulet'
    >>> _name_simple("Asperge", Technique.FOUR, RestaurantType.BISTRO)
    'Asperge rôti'
    """
    # petits templates selon concept
    if rtype == RestaurantType.FAST_FOOD:
        if "Boeuf haché" in ing_name:
            return "Burger classique"
        if "Poulet" in ing_name:
            return "Burger de poulet"
        if "Cabillaud" in ing_name:
            return "Fish & Chips"
    # générique
    base = {
        Technique.GRILLE: "grillé",
        Technique.SAUTE: "poêlé",
        Technique.FOUR: "rôti",
        Technique.FROID: "froid",
    }[tech]
    return f"{ing_name} {base}"


def _name_combo(a: str, b: str, tech: Technique, rtype: RestaurantType) -> str:
    """Construit un nom lisible pour une recette combo.

    Paramètres
    ----------
    a, b : str
        Noms des deux ingrédients.
    tech : Technique
        Technique retenue pour le combo.
    rtype : RestaurantType
        Type de restaurant (influe sur la mise en forme du nom).

    Retour
    ------
    str
        Intitulé lisible du combo.

    Notes
    -----
    En ``GASTRO``, la conjonction « & » et une ponctuation plus valorisante
    sont utilisées.

    Exemple
    -------
    >>> _name_combo("Saumon", "Asperge", Technique.FOUR, RestaurantType.BISTRO)
    'Saumon + Asperge (au four)'
    >>> _name_combo("Saumon", "Asperge", Technique.FOUR, RestaurantType.GASTRO)
    'Saumon & Asperge, au four'
    """
    label = {
        Technique.GRILLE: "grillé",
        Technique.SAUTE: "poêlé",
        Technique.FOUR: "au four",
        Technique.FROID: "froid",
    }[tech]
    # gastro: noms valorisants
    if rtype == RestaurantType.GASTRO:
        return f"{a} & {b}, {label}"
    return f"{a} + {b} ({label})"


def _choose_grade(
    prices_by_grade: Dict[FoodGrade, float], rtype: RestaurantType
) -> FoodGrade:
    """Choisit une gamme d'ingrédient cohérente avec le type de resto.

    Paramètres
    ----------
    prices_by_grade : Dict[FoodGrade, float]
        Prix au kg disponibles par gamme pour l'ingrédient.
    rtype : RestaurantType
        Type de restaurant, conditionnant l'ordre de préférence.

    Retour
    ------
    FoodGrade
        Gamme sélectionnée parmi celles disponibles.

    Notes
    -----
    Préférences par défaut:
    - ``FAST_FOOD``: pratique/surgelé prioritaire
    - ``BISTRO``: frais prioritaire, puis surgelé
    - ``GASTRO``: frais prioritaire

    Exemple
    -------
    >>> from FoodOPS_V1.domain.ingredients import FoodGrade
    >>> _choose_grade({FoodGrade.G1_FRAIS_BRUT: 7.5, FoodGrade.G3_SURGELE: 6.2}, RestaurantType.FAST_FOOD) in (FoodGrade.G3_SURGELE, FoodGrade.G1_FRAIS_BRUT)
    True
    """
    # Ordre de préférence par type de restaurant
    preferences = {
        RestaurantType.FAST_FOOD: [FoodGrade.G3_SURGELE, FoodGrade.G1_FRAIS_BRUT],
        RestaurantType.BISTRO: [FoodGrade.G1_FRAIS_BRUT, FoodGrade.G3_SURGELE],
        RestaurantType.GASTRO: [FoodGrade.G1_FRAIS_BRUT, FoodGrade.G3_SURGELE],
    }

    available_grades = set(prices_by_grade.keys())
    for grade in preferences[rtype]:
        if grade in available_grades:
            return grade

    # Fallback: première gamme disponible
    return next(iter(prices_by_grade))


def _fit_for_ing(ing_name: str, rtype: RestaurantType) -> float:
    """Retourne un score de fit catalogue (0..1) pour un ingrédient et un concept.

    Paramètres
    ----------
    ing_name : str
        Nom de l'ingrédient dans le catalogue.
    rtype : RestaurantType
        Type de restaurant.

    Retour
    ------
    float
        Score de compatibilité catalogue pour ce concept (défaut à 0.7).

    Exemple
    -------
    >>> _fit_for_ing("Poulet", RestaurantType.FAST_FOOD)
    1.0
    """
    item = CATALOG[ing_name]
    key = rtype.name  # "FAST_FOOD" | "BISTRO" | "GASTRO"
    return float(item.fit_score.get(key, 0.7))


def _quality_from_ings(ings: List[str], rtype: RestaurantType) -> float:
    """Estime une qualité perçue basée sur le fit moyen des ingrédients.

    Paramètres
    ----------
    ings : List[str]
        Noms des ingrédients utilisés.
    rtype : RestaurantType
        Type de restaurant servant pour le calcul des fits.

    Retour
    ------
    float
        Qualité perçue, bornée grossièrement entre 0 et 1.

    Notes
    -----
    Calcul: moyenne des ``_fit_for_ing`` multipliée par une base 0.7.

    Exemple
    -------
    >>> round(_quality_from_ings(["Poulet", "Pomme de terre"], RestaurantType.FAST_FOOD), 3)
    0.7
    """
    # qualité perçue = moyenne des fit * un petit base (0.7)
    if not ings:
        return 0.0
    fits = [_fit_for_ing(n, rtype) for n in ings]
    return round(0.7 * (sum(fits) / len(fits)), 3)


def _cost_per_portion(ing_name: str, grade: FoodGrade) -> float:
    """Coût matière par portion pour un ingrédient/grade.

    Paramètres
    ----------
    ing_name : str
        Nom de l'ingrédient dans le catalogue.
    grade : FoodGrade
        Gamme choisie pour l'ingrédient.

    Retour
    ------
    float
        Coût matière par portion, en unité monétaire du catalogue.

    Notes
    -----
    La portion (kg) est approchée via `PORTION_KG` par catégorie principale.
    Par défaut, une portion de 0.08 kg est utilisée si la catégorie n'est pas listée.

    Exemple
    -------
    >>> from FoodOPS_V1.domain.ingredients import FoodGrade
    >>> _cost_per_portion("Poulet", FoodGrade.G1_FRAIS_BRUT)
    1.12
    """
    item = CATALOG[ing_name]
    price_kg = item.prices_by_grade[grade]
    cats = item.categories
    # si plusieurs catégories, prend la 1ère pour la portion
    portion = PORTION_KG.get(cats[0], 0.08)
    return round(price_kg * portion, 2)


def _compute_price(
    cost_per_portion: float, rtype: RestaurantType, complexity: Complexity
) -> float:
    """Applique un multiplicateur type concept pour obtenir un prix TTC indicatif.

    Paramètres
    ----------
    cost_per_portion : float
        Coût matière estimé par portion.
    rtype : RestaurantType
        Type de restaurant (détermine la marge de base).
    complexity : Complexity
        Complexité de la recette (peut ajuster la marge).

    Retour
    ------
    float
        Prix de vente indicatif TTC.

    Notes
    -----
    Un supplément de marge est appliqué aux combos pour refléter la valeur perçue.

    Exemple
    -------
    >>> _compute_price(1.2, RestaurantType.FAST_FOOD, Complexity.SIMPLE)
    3.0
    """
    mult = MARGIN_BY_RESTO[rtype]
    if complexity == Complexity.COMBO:
        mult += 0.4
    return round(cost_per_portion * mult, 2)


def _gen_simple(item: Ingredient, rtype: RestaurantType) -> SimpleRecipe:
    """Crée une recette simple à partir d'un item de catalogue.

    Paramètres
    ----------
    item : Ingredient
        Item issu du catalogue (contient prix/grades, catégories, nom).
    rtype : RestaurantType
        Type de restaurant cible.

    Retour
    ------
    SimpleRecipe
        Recette simple prête à être affichée dans un menu.

    Exemple
    -------
    >>> it = CATALOG["Poulet"]
    >>> rec = _gen_simple(it, RestaurantType.FAST_FOOD)
    >>> isinstance(rec, SimpleRecipe)
    True
    """
    # pick une gamme cohérente
    grade = _choose_grade(item.prices_by_grade, rtype)
    tech = random.choice(_TECH_BY_CAT[item.categories[0]])
    name = _name_simple(item.name, tech, rtype)
    c_per_portion = _cost_per_portion(item.name, grade)
    price = _compute_price(c_per_portion, rtype, Complexity.SIMPLE)
    qual = _quality_from_ings([item.name], rtype)

    return SimpleRecipe(
        name=name,
        ingredients=[(item.name, grade)],
        technique=tech,
        complexity=Complexity.SIMPLE,
        base_quality=qual,
        price=price,
    )


def _compatible(a: Ingredient, b: Ingredient) -> bool:
    """Retourne True si les catégories primaires sont compatibles pour un combo.

    Paramètres
    ----------
    a, b : Ingredient
        Deux items du catalogue à associer.

    Retour
    ------
    bool
        ``True`` si la paire de catégories principales est autorisée.

    Notes
    -----
    La compatibilité est vérifiée sur la catégorie à l'index 0 de chaque item
    et est symétrique (A,B) ≡ (B,A).

    Exemple
    -------
    >>> _compatible(CATALOG["Saumon"], CATALOG["Asperge"])  # poisson+legume
    True
    >>> _compatible(CATALOG["Saumon"], CATALOG["Beurre"])  # poisson+laitier
    False
    """
    ca = a.categories[0]
    cb = b.categories[0]
    pair = (ca, cb)
    rev = (cb, ca)
    return pair in _ALLOWED_COMBOS or rev in _ALLOWED_COMBOS


def _gen_combo(a: Ingredient, b: Ingredient, rtype: RestaurantType) -> SimpleRecipe:
    """Crée une recette combo à partir de deux items compatibles.

    Paramètres
    ----------
    a, b : Ingredient
        Items compatibles à associer dans la recette.
    rtype : RestaurantType
        Type de restaurant cible.

    Retour
    ------
    SimpleRecipe
        Recette « combo » combinant les deux ingrédients.

    Notes
    -----
    La technique est choisie dans l'intersection des techniques possibles
    pour chaque catégorie primaire, avec repli sur ``SAUTE`` s'il n'y a pas
    d'intersection.

    Exemple
    -------
    >>> a, b = CATALOG["Saumon"], CATALOG["Asperge"]
    >>> rec = _gen_combo(a, b, RestaurantType.BISTRO)
    >>> isinstance(rec, SimpleRecipe)
    True
    """
    grade_a = _choose_grade(a.prices_by_grade, rtype)
    grade_b = _choose_grade(b.prices_by_grade, rtype)
    tech = random.choice(
        list(set(_TECH_BY_CAT[a.categories[0]]) & set(_TECH_BY_CAT[b.categories[0]]))
        or [Technique.SAUTE]
    )

    name = _name_combo(a.name, b.name, tech, rtype)
    c_portion = _cost_per_portion(a.name, grade_a) + _cost_per_portion(b.name, grade_b)
    price = _compute_price(c_portion, rtype, Complexity.COMBO)
    qual = _quality_from_ings([a.name, b.name], rtype)

    return SimpleRecipe(
        name=name,
        ingredients=[(a.name, grade_a), (b.name, grade_b)],
        technique=tech,
        complexity=Complexity.COMBO,
        base_quality=qual,
        price=price,
    )


def build_menu_for_type(rtype: RestaurantType) -> List[SimpleRecipe]:
    """Génère un menu varié pour un type de restaurant donné.

    Crée un menu équilibré composé de recettes simples et de combos,
    adapté au niveau et au style du type de restaurant. Le nombre de
    recettes varie selon le type : 10 pour fast-food, 15 pour bistro,
    20 pour gastro.

    Paramètres
    ----------
    rtype : RestaurantType
        Type de restaurant (FAST_FOOD, BISTRO, ou GASTRO) qui détermine
        la taille du menu et les ingrédients accessibles.

    Retour
    ------
    List[SimpleRecipe]
        Liste de recettes variées pour le menu, contenant un mélange
        de recettes simples et de combos adaptés au type de restaurant.

    Notes
    -----
    - Varie l'ordre des ingrédients via un mélange pour obtenir des menus
      différents d'une exécution à l'autre.
    - Tentative exhaustive de paires compatibles jusqu'à atteindre la taille
      cible, puis repli sur des recettes simples si nécessaire (fail-safe).

    Exemple
    -------
    >>> menu = build_menu_for_type(RestaurantType.FAST_FOOD)
    >>> len(menu) == 10 and all(isinstance(m, SimpleRecipe) for m in menu)
    True
    >>> menu = build_menu_for_type(RestaurantType.GASTRO)
    >>> len(menu) == 20
    True
    """
    # Définir la taille cible du menu selon le type de restaurant
    targets = {
        RestaurantType.FAST_FOOD: 10,
        RestaurantType.BISTRO: 15,
        RestaurantType.GASTRO: 20,
    }
    target = targets[rtype]

    # Filtrer le catalogue pour ne garder que les ingrédients accessibles au type de restaurant.
    # (Réduit l'espace de recherche et évite de proposer des items inadaptés au concept.)
    avail = [it for it in CATALOG.values() if _allowed_for_type(it, rtype)]
    random.shuffle(avail)  # Mélanger pour varier les menus à chaque génération

    # 1) Générer des recettes simples (environ la moitié du menu, minimum 6)
    # Prendre les premiers ingrédients disponibles après mélange
    nombre_recettes_simples = max(6, target // 2)
    simples = [_gen_simple(it, rtype) for it in avail[:nombre_recettes_simples]]

    # 2) Générer des combos en testant toutes les paires d'ingrédients compatibles.
    #    On s'arrête dès que la taille cible est atteinte pour éviter un coût quadratique inutile.
    combos: List[SimpleRecipe] = []
    for i in range(len(avail)):
        for j in range(i + 1, len(avail)):
            # Arrêter si on a atteint la taille cible du menu
            if len(simples) + len(combos) >= target:
                break

            # Tester la compatibilité des deux ingrédients (catégories primaires)
            a, b = avail[i], avail[j]
            if _compatible(a, b):
                combos.append(_gen_combo(a, b, rtype))

        # Double vérification pour sortir de la boucle externe
        if len(simples) + len(combos) >= target:
            break

    # Combiner simples et combos, en limitant à la taille cible
    menu = (simples + combos)[:target]

    # Fail-safe : si on n'a pas assez de recettes (manque de combos compatibles),
    # compléter avec des recettes simples aléatoires pour atteindre la cible.
    while len(menu) < target:
        menu.append(_gen_simple(random.choice(avail), rtype))

    return menu
