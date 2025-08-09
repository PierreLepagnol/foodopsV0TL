# -*- coding: utf-8 -*-
# foodops/rules/recipes_factory.py
from dataclasses import dataclass
from typing import List, Tuple, Dict
import random

from ..domain.simple_recipe import SimpleRecipe, Technique, Complexity
from ..domain.restaurant import RestaurantType
from ..data.ingredients_catalog import CATALOG, CatalogItem
from ..domain.ingredients import IngredientCategory, FoodGrade

# ---------------- Compatibilités & styles ----------------

_ALLOWED_COMBOS: Tuple[Tuple[IngredientCategory, IngredientCategory], ...] = (
    (IngredientCategory.VIANDE, IngredientCategory.LEGUME),
    (IngredientCategory.VIANDE, IngredientCategory.FECULENT),
    (IngredientCategory.POISSON, IngredientCategory.LEGUME),
    (IngredientCategory.POISSON, IngredientCategory.FECULENT),
)

_TECH_BY_CAT = {
    IngredientCategory.VIANDE: [Technique.GRILLE, Technique.SAUTE],
    IngredientCategory.POISSON: [Technique.FOUR, Technique.SAUTE, Technique.FROID],
    IngredientCategory.LEGUME: [Technique.FOUR, Technique.SAUTE, Technique.FROID],
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

def _allowed_for_type(item: CatalogItem, rtype: RestaurantType) -> bool:
    if item.tier == "ALL":
        return True
    if item.tier == "BISTRO+" and rtype in (RestaurantType.BISTRO, RestaurantType.GASTRO):
        return True
    if item.tier == "GASTRO_ONLY" and rtype == RestaurantType.GASTRO:
        return True
    return False

def _name_simple(ing_name: str, tech: Technique, rtype: RestaurantType) -> str:
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

def _choose_grade(prices_by_grade: Dict[FoodGrade, float], rtype: RestaurantType) -> FoodGrade:
    # simple règle: FF préfère G3 (praticité), Bistro mix, Gastro préfère G1
    grades = list(prices_by_grade.keys())
    if rtype == RestaurantType.FAST_FOOD:
        pref = [FoodGrade.G3_SURGELE, FoodGrade.G1_FRAIS_BRUT]
    elif rtype == RestaurantType.BISTRO:
        pref = [FoodGrade.G1_FRAIS_BRUT, FoodGrade.G3_SURGELE]
    else:
        pref = [FoodGrade.G1_FRAIS_BRUT, FoodGrade.G3_SURGELE]
    for p in pref:
        if p in grades:
            return p
    return grades[0]

def _fit_for_ing(ing_name: str, rtype: RestaurantType) -> float:
    item = CATALOG[ing_name]
    key = rtype.name  # "FAST_FOOD" | "BISTRO" | "GASTRO"
    return float(item.fit_score.get(key, 0.7))

def _quality_from_ings(ings: List[str], rtype: RestaurantType) -> float:
    # qualité perçue = moyenne des fit * un petit base (0.7)
    if not ings:
        return 0.0
    fits = [_fit_for_ing(n, rtype) for n in ings]
    return round(0.7 * (sum(fits)/len(fits)), 3)

def _cost_per_portion(ing_name: str, grade: FoodGrade) -> float:
    item = CATALOG[ing_name]
    price_kg = item.prices_by_grade[grade]
    cats = item.categories
    # si plusieurs catégories, prend la 1ère pour la portion
    portion = PORTION_KG.get(cats[0], 0.08)
    return round(price_kg * portion, 2)

def _compute_price(cost_per_portion: float, rtype: RestaurantType, complexity: Complexity) -> float:
    mult = MARGIN_BY_RESTO[rtype]
    if complexity == Complexity.COMBO:
        mult += 0.4
    return round(cost_per_portion * mult, 2)

def _gen_simple(item: CatalogItem, rtype: RestaurantType) -> SimpleRecipe:
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

def _compatible(a: CatalogItem, b: CatalogItem) -> bool:
    ca = a.categories[0]; cb = b.categories[0]
    pair = (ca, cb)
    rev = (cb, ca)
    return pair in _ALLOWED_COMBOS or rev in _ALLOWED_COMBOS

def _gen_combo(a: CatalogItem, b: CatalogItem, rtype: RestaurantType) -> SimpleRecipe:
    grade_a = _choose_grade(a.prices_by_grade, rtype)
    grade_b = _choose_grade(b.prices_by_grade, rtype)
    tech = random.choice(list(set(_TECH_BY_CAT[a.categories[0]]) & set(_TECH_BY_CAT[b.categories[0]])) or [Technique.SAUTE])

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
    # cible de longueur de menu selon type
    targets = {
        RestaurantType.FAST_FOOD: 10,
        RestaurantType.BISTRO: 15,
        RestaurantType.GASTRO: 20,
    }
    target = targets[rtype]

    # filtre catalogue selon tier d’accès
    avail = [it for it in CATALOG.values() if _allowed_for_type(it, rtype)]
    random.shuffle(avail)

    # 1) simples
    simples = [_gen_simple(it, rtype) for it in avail[:max(6, target // 2)]]

    # 2) combos compatibles
    combos: List[SimpleRecipe] = []
    for i in range(len(avail)):
        for j in range(i+1, len(avail)):
            if len(simples) + len(combos) >= target:
                break
            a, b = avail[i], avail[j]
            if _compatible(a, b):
                combos.append(_gen_combo(a, b, rtype))
        if len(simples) + len(combos) >= target:
            break

    menu = (simples + combos)[:target]
    # fail-safe: si pas assez de combos, rajoute des simples au pif
    while len(menu) < target:
        menu.append(_gen_simple(random.choice(avail), rtype))
    return menu
