# -*- coding: utf-8 -*-
# foodops/data/ingredients_catalog.py
from dataclasses import dataclass
from typing import Dict, List
from ..domain.ingredients import IngredientCategory, FoodGrade

# ---- Modèle local d'item du catalogue (on ne touche pas à ton dataclass Ingredient du domaine) ----

@dataclass(frozen=True)
class CatalogItem:
    name: str
    categories: List[IngredientCategory]
    # prix €/kg par gamme disponible
    prices_by_grade: Dict[FoodGrade, float]
    # DLC indicative (jours)
    perish_days: int
    # fit qualité perçue selon type de restaurant (coeff 0..1)
    fit_score: Dict[str, float]  # clés: "FAST_FOOD" | "BISTRO" | "GASTRO"
    # niveau "tiers" d’accès: "ALL", "BISTRO+", "GASTRO_ONLY"
    tier: str = "ALL"

# Helper pour factoriser des dicts prix
def _pg(**kwargs):
    # usage: _pg(G1_FRAIS_BRUT=xx, G3_SURGELE=yy, ...)
    return {getattr(FoodGrade, k): v for k, v in kwargs.items()}

# ---------------------------------------
# CATALOGUE — Standard + Premium
# ---------------------------------------
CATALOG: Dict[str, CatalogItem] = {
    # —— Viandes / Volailles
    "Poulet": CatalogItem(
        name="Poulet",
        categories=[IngredientCategory.VIANDE],
        prices_by_grade=_pg(G1_FRAIS_BRUT=7.5, G3_SURGELE=6.2),
        perish_days=5,
        fit_score={"FAST_FOOD": 1.00, "BISTRO": 0.85, "GASTRO": 0.70},
        tier="ALL",
    ),
    "Boeuf haché": CatalogItem(
        name="Boeuf haché",
        categories=[IngredientCategory.VIANDE],
        prices_by_grade=_pg(G1_FRAIS_BRUT=10.5, G3_SURGELE=9.0),
        perish_days=4,
        fit_score={"FAST_FOOD": 1.00, "BISTRO": 0.80, "GASTRO": 0.60},
        tier="ALL",
    ),
    "Filet de boeuf": CatalogItem(
        name="Filet de boeuf",
        categories=[IngredientCategory.VIANDE],
        prices_by_grade=_pg(G1_FRAIS_BRUT=34.0, G3_SURGELE=28.0),
        perish_days=5,
        fit_score={"FAST_FOOD": 0.50, "BISTRO": 0.85, "GASTRO": 1.00},
        tier="BISTRO+",
    ),
    "Magret de canard": CatalogItem(
        name="Magret de canard",
        categories=[IngredientCategory.VIANDE],
        prices_by_grade=_pg(G1_FRAIS_BRUT=22.0, G3_SURGELE=18.5),
        perish_days=5,
        fit_score={"FAST_FOOD": 0.55, "BISTRO": 0.90, "GASTRO": 0.95},
        tier="BISTRO+",
    ),

    # —— Poissons / Coquillages
    "Saumon": CatalogItem(
        name="Saumon",
        categories=[IngredientCategory.POISSON],
        prices_by_grade=_pg(G1_FRAIS_BRUT=18.0, G3_SURGELE=14.5),
        perish_days=3,
        fit_score={"FAST_FOOD": 0.70, "BISTRO": 0.90, "GASTRO": 0.95},
        tier="ALL",
    ),
    "Cabillaud": CatalogItem(
        name="Cabillaud",
        categories=[IngredientCategory.POISSON],
        prices_by_grade=_pg(G1_FRAIS_BRUT=16.0, G3_SURGELE=12.0),
        perish_days=3,
        fit_score={"FAST_FOOD": 0.75, "BISTRO": 0.90, "GASTRO": 0.90},
        tier="ALL",
    ),
    "Saint-Jacques": CatalogItem(
        name="Saint-Jacques",
        categories=[IngredientCategory.POISSON],
        prices_by_grade=_pg(G1_FRAIS_BRUT=38.0, G3_SURGELE=30.0),
        perish_days=3,
        fit_score={"FAST_FOOD": 0.50, "BISTRO": 0.85, "GASTRO": 1.00},
        tier="BISTRO+",
    ),
    "Homard": CatalogItem(
        name="Homard",
        categories=[IngredientCategory.POISSON],
        prices_by_grade=_pg(G1_FRAIS_BRUT=60.0, G3_SURGELE=48.0),
        perish_days=2,
        fit_score={"FAST_FOOD": 0.30, "BISTRO": 0.75, "GASTRO": 1.00},
        tier="GASTRO_ONLY",
    ),

    # —— “Luxe”
    "Foie gras": CatalogItem(
        name="Foie gras",
        categories=[IngredientCategory.VIANDE],
        prices_by_grade=_pg(G1_FRAIS_BRUT=60.0, G3_SURGELE=50.0),
        perish_days=7,
        fit_score={"FAST_FOOD": 0.40, "BISTRO": 0.80, "GASTRO": 1.00},
        tier="GASTRO_ONLY",
    ),
    "Truffe noire": CatalogItem(
        name="Truffe noire",
        categories=[IngredientCategory.CONDIMENT],
        prices_by_grade=_pg(G1_FRAIS_BRUT=900.0),
        perish_days=10,
        fit_score={"FAST_FOOD": 0.10, "BISTRO": 0.70, "GASTRO": 1.00},
        tier="GASTRO_ONLY",
    ),

    # —— Légumes & Accompagnements
    "Pomme de terre": CatalogItem(
        name="Pomme de terre",
        categories=[IngredientCategory.LEGUME],
        prices_by_grade=_pg(G1_FRAIS_BRUT=1.5, G3_SURGELE=1.8),
        perish_days=20,
        fit_score={"FAST_FOOD": 1.00, "BISTRO": 0.95, "GASTRO": 0.85},
        tier="ALL",
    ),
    "Riz": CatalogItem(
        name="Riz",
        categories=[IngredientCategory.FECULENT],
        prices_by_grade=_pg(G3_SURGELE=2.0),  # on modélise “sec” via G3
        perish_days=180,
        fit_score={"FAST_FOOD": 0.95, "BISTRO": 0.95, "GASTRO": 0.90},
        tier="ALL",
    ),
    "Asperge": CatalogItem(
        name="Asperge",
        categories=[IngredientCategory.LEGUME],
        prices_by_grade=_pg(G1_FRAIS_BRUT=9.0, G3_SURGELE=7.0),
        perish_days=4,
        fit_score={"FAST_FOOD": 0.60, "BISTRO": 0.90, "GASTRO": 0.95},
        tier="BISTRO+",
    ),

    # —— Laitiers / Boulangerie
    "Beurre": CatalogItem(
        name="Beurre",
        categories=[IngredientCategory.PRODUIT_LAITIER],
        prices_by_grade=_pg(G1_FRAIS_BRUT=5.5),
        perish_days=30,
        fit_score={"FAST_FOOD": 0.90, "BISTRO": 1.00, "GASTRO": 1.00},
        tier="ALL",
    ),
    "Pain burger": CatalogItem(
        name="Pain burger",
        categories=[IngredientCategory.BOULANGERIE],
        prices_by_grade=_pg(G3_SURGELE=3.2),
        perish_days=20,
        fit_score={"FAST_FOOD": 1.00, "BISTRO": 0.70, "GASTRO": 0.40},
        tier="ALL",
    ),
}
