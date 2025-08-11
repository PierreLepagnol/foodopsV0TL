from enum import Enum, auto

from dataclasses import dataclass
from typing import Dict, List
from FoodOPS_V1.domain.restaurant import RestaurantType


"""
Catalogue d'ingrédients multi-gammes + perception qualité selon type de restaurant.
Catalogue d'ingrédients et de catégories pour le jeu FoodOPS
"""


class IngredientCategory(Enum):
    VIANDE = auto()
    POISSON = auto()
    LEGUME = auto()
    FECULENT = auto()
    LEGUMINEUSE = auto()
    PRODUIT_LAITIER = auto()
    CONDIMENT = auto()
    BOULANGERIE = auto()
    AUTRE = auto()


class FoodGrade(Enum):
    """Gammes pro FR (1→5)."""

    G1_FRAIS_BRUT = auto()  # frais bruts
    G2_CONSERVE = auto()  # conserve/semi-conserve
    G3_SURGELE = auto()  # surgelé
    G4_CRU_PRET = auto()  # cru prêt à l'emploi
    G5_CUIT_SOUS_VIDE = auto()  # cuit/vide/régénération


@dataclass(frozen=True)
class Ingredient:
    name: str
    base_priceformat_currency_eur_per_kg: float
    category: IngredientCategory
    grade: FoodGrade
    perish_days: int


# Coefficients de perception qualité selon le type de resto et la gamme
# 1.0 = qualité perçue optimale, < 1.0 = perçu comme moins qualitatif
QUALITY_PERCEPTION: Dict[RestaurantType, Dict[FoodGrade, float]] = {
    RestaurantType.FAST_FOOD: {
        FoodGrade.G1_FRAIS_BRUT: 1.0,
        FoodGrade.G2_CONSERVE: 0.9,
        FoodGrade.G3_SURGELE: 0.95,
        FoodGrade.G4_CRU_PRET: 1.0,
        FoodGrade.G5_CUIT_SOUS_VIDE: 0.95,
    },
    RestaurantType.BISTRO: {
        FoodGrade.G1_FRAIS_BRUT: 1.0,
        FoodGrade.G2_CONSERVE: 0.8,
        FoodGrade.G3_SURGELE: 0.85,
        FoodGrade.G4_CRU_PRET: 0.95,
        FoodGrade.G5_CUIT_SOUS_VIDE: 0.9,
    },
    RestaurantType.GASTRO: {
        FoodGrade.G1_FRAIS_BRUT: 1.0,
        FoodGrade.G2_CONSERVE: 0.6,
        FoodGrade.G3_SURGELE: 0.5,  # saumon surgelé en gastro => grosse pénalité
        FoodGrade.G4_CRU_PRET: 0.85,
        FoodGrade.G5_CUIT_SOUS_VIDE: 0.8,
    },
}

# ----------------------------------------------------------------------
# Catalogue multi-gammes
# ----------------------------------------------------------------------


def get_all_ingredients() -> List[Ingredient]:
    """
    Retourne une liste d'ingrédients avec plusieurs gammes disponibles.
    """
    ingredients: List[Ingredient] = []

    # Viandes
    ingredients += [
        Ingredient(
            "Steak haché",
            12.0,
            IngredientCategory.VIANDE,
            FoodGrade.G1_FRAIS_BRUT,
            5,
        ),
        Ingredient(
            "Steak haché",
            9.0,
            IngredientCategory.VIANDE,
            FoodGrade.G3_SURGELE,
            180,
        ),
        Ingredient(
            "Poulet",
            11.0,
            IngredientCategory.VIANDE,
            FoodGrade.G1_FRAIS_BRUT,
            5,
        ),
        Ingredient("Poulet", 8.0, IngredientCategory.VIANDE, FoodGrade.G3_SURGELE, 180),
    ]

    # Poissons
    ingredients += [
        Ingredient(
            "Saumon",
            20.0,
            IngredientCategory.POISSON,
            FoodGrade.G1_FRAIS_BRUT,
            3,
        ),
        Ingredient(
            "Saumon",
            15.0,
            IngredientCategory.POISSON,
            FoodGrade.G3_SURGELE,
            180,
        ),
        Ingredient(
            "Cabillaud",
            16.0,
            IngredientCategory.POISSON,
            FoodGrade.G1_FRAIS_BRUT,
            3,
        ),
        Ingredient(
            "Cabillaud",
            12.0,
            IngredientCategory.POISSON,
            FoodGrade.G3_SURGELE,
            180,
        ),
    ]

    # Féculents
    ingredients += [
        Ingredient("Riz", 2.5, IngredientCategory.FECULENT, FoodGrade.G2_CONSERVE, 365),
        Ingredient("Riz", 2.0, IngredientCategory.FECULENT, FoodGrade.G3_SURGELE, 180),
    ]

    # Produits laitiers
    ingredients += [
        Ingredient(
            "Fromage cheddar",
            7.0,
            IngredientCategory.PRODUIT_LAITIER,
            FoodGrade.G3_SURGELE,
            180,
        ),
        Ingredient(
            "Fromage cheddar",
            8.5,
            IngredientCategory.PRODUIT_LAITIER,
            FoodGrade.G1_FRAIS_BRUT,
            15,
        ),
    ]

    # oeufs
    ingredients += [
        Ingredient(
            "oeufs",
            4.0,
            IngredientCategory.PRODUIT_LAITIER,
            FoodGrade.G1_FRAIS_BRUT,
            15,
        ),
        Ingredient(
            "oeufs",
            5.5,
            IngredientCategory.PRODUIT_LAITIER,
            FoodGrade.G5_CUIT_SOUS_VIDE,
            60,
        ),
    ]

    return ingredients
