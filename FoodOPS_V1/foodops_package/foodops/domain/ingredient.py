from dataclasses import dataclass
from enum import Enum, auto


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
    """Gammes pro FR (1→5). On s’en sert pour coût/qualité/coût de main d’œuvre implicite."""
    # NB: Les multiplicateurs fins sont dans rules/costing.py
    G1_FRAIS_BRUT = auto()        # 1ère gamme : frais bruts
    G2_CONSERVE = auto()          # 2e gamme : conserve/semi-conserve
    G3_SURGELE = auto()           # 3e gamme : surgelé
    G4_CRU_PRET = auto()          # 4e gamme : cru prêt à l'emploi
    G5_CUIT_SOUS_VIDE = auto()    # 5e gamme : cuit/vide/régénération


@dataclass(frozen=True)
class Ingredient:
    name: str
    base_price_eur_per_kg: float
    category: IngredientCategory
    grade: FoodGrade
    perish_days: int  # DLC/DLUO indicative (on affinera avec stock plus tard)
