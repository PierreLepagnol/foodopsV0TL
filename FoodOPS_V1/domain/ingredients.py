# foodops/domain/ingredients.py
"""
Définitions de base (Enums + dataclass Ingredient) ET pont vers le catalogue FR.
D'autres modules importent parfois `foodops.domain.ingredients`, donc on ré-exporte
les fonctions/datas utiles (QUALITY_PERCEPTION, get_all_ingredients) depuis data/ingredients_fr.
"""

import json
from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, field_validator, ValidationError


class IngredientCategory(Enum):
    VIANDE = "VIANDE"
    POISSON = "POISSON"
    LEGUME = "LEGUME"
    FECULENT = "FECULENT"
    LEGUMINEUSE = "LEGUMINEUSE"
    PRODUIT_LAITIER = "PRODUIT_LAITIER"
    CONDIMENT = "CONDIMENT"
    BOULANGERIE = "BOULANGERIE"
    AUTRE = "AUTRE"


class FoodGrade(Enum):
    """Gammes pro FR (1→5). On s'en sert pour coût/qualité/coût de main d'oeuvre implicite."""

    # NB: Les multiplicateurs fins sont dans rules/costing.py
    G1_FRAIS_BRUT = "G1_FRAIS_BRUT"  # 1ère gamme : frais bruts
    G2_CONSERVE = "G2_CONSERVE"  # 2e gamme : conserve/semi-conserve
    G3_SURGELE = "G3_SURGELE"  # 3e gamme : surgelé
    G4_CRU_PRET = "G4_CRU_PRET"  # 4e gamme : cru prêt à l'emploi
    G5_CUIT_SOUS_VIDE = "G5_CUIT_SOUS_VIDE"  # 5e gamme : cuit/vide/régénération


class IngredientTier(BaseModel):
    """Represents the tier/access level for ingredients in different restaurant types."""

    ALL: str = "ALL"
    BISTRO_PLUS: str = "BISTRO+"
    GASTRO_ONLY: str = "GASTRO_ONLY"


class FitScoreKeys(BaseModel):
    """Represents the restaurant types used for fit scoring."""

    FAST_FOOD: str = "FAST_FOOD"
    BISTRO: str = "BISTRO"
    GASTRO: str = "GASTRO"


class CatalogConfig(BaseModel):
    """Configuration model for ingredient catalog validation."""

    tiers_allowed: List[str] = ["ALL", "BISTRO+", "GASTRO_ONLY"]
    fit_score_keys: List[str] = ["FAST_FOOD", "BISTRO", "GASTRO"]

    @field_validator("tiers_allowed")
    @classmethod
    def validate_tiers(cls, v):
        allowed_tiers = {"ALL", "BISTRO+", "GASTRO_ONLY"}
        for tier in v:
            if tier not in allowed_tiers:
                raise ValueError(
                    f"Invalid tier: {tier}. Must be one of {allowed_tiers}"
                )
        return v

    @field_validator("fit_score_keys")
    @classmethod
    def validate_fit_keys(cls, v):
        allowed_keys = {"FAST_FOOD", "BISTRO", "GASTRO"}
        for key in v:
            if key not in allowed_keys:
                raise ValueError(
                    f"Invalid fit score key: {key}. Must be one of {allowed_keys}"
                )
        return v


class Ingredient(BaseModel):
    name: str
    categories: List[IngredientCategory]
    prices_by_grade: Dict[FoodGrade, float]
    perish_days: int
    fit_score: Dict[str, float]
    tier: str = "ALL"
    # grade: FoodGrade

    # base_priceformat_currency_eur_per_kg: float


def load_catalog_config(filepath: str) -> Dict[str, Ingredient]:
    """Charge la configuration du catalogue d'ingrédients depuis un fichier JSON.

    Lit un fichier JSON contenant la configuration des ingrédients et retourne
    un dictionnaire structuré avec validation Pydantic.

    Paramètres
    ----------
    filepath : str
        Chemin vers le fichier JSON de configuration du catalogue.

    Retour
    ------
    Dict[str, Ingredient]
        Dictionnaire mappant chaque nom d'ingrédient à son objet Ingredient.

    Exemple
    -------
    >>> config = load_catalog_config("catalog_config.json")
    >>> "Poulet" in config
    True
    >>> isinstance(config["Poulet"], Ingredient)
    True

    Lève
    ----
    FileNotFoundError
        Si le fichier de configuration n'existe pas.
    ValueError
        Si les données du JSON ne sont pas valides selon le modèle Ingredient.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    catalog: Dict[str, Ingredient] = {}
    for ingredient_name, ingredient_data in raw_data.items():
        try:
            # Ajout du nom de l'ingrédient aux données
            ingredient_data["name"] = ingredient_name
            catalog[ingredient_name] = Ingredient.model_validate(ingredient_data)
        except ValidationError as e:
            raise ValueError(f"Validation error for ingredient {ingredient_name}: {e}")

    return catalog


CATALOG = load_catalog_config(
    "/home/lepagnol/Documents/Perso/Games/foodopsV0TL/FoodOPS_V1/data/catalog_config.json"
)
