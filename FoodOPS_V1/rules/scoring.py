from pathlib import Path
from typing import Annotated, Dict, Optional

import numpy as np
from pydantic import BaseModel, Field

from FoodOPS_V1.domain.restaurant import Restaurant
from FoodOPS_V1.domain.market import BUDGET_PER_SEGMENT, Segment
from FoodOPS_V1.domain.types import RestaurantType
from FoodOPS_V1.domain.recipe import SimpleRecipe
from FoodOPS_V1.utils import load_and_validate

# ==========================
# Poids des critères (somme ~ 1)
# ==========================


# ==========================
# Petits helpers génériques
# ==========================

# =====================================================
# Qualité perçue du menu
#  - Combine la qualité des recettes (moyenne)
#  - Applique un ajustement "exigence du concept"
#  - Applique la satisfaction RH (optionnelle)
# =====================================================


def _recipe_grade_hint(recipe: SimpleRecipe) -> Optional[str]:
    """
    Retourne un hint de "gamme ingrédient" si disponible.
    Ex. 'G1','G3','G5' ou 'fresh','frozen','sousvide'. None si indéterminé.

    Exemple
    -------
    'G3'
    """
    # Essais souples de champs potentiels
    for attr in ("grade_hint", "grade_tag", "grade", "food_grade", "ing_grade"):
        v = getattr(recipe, attr, None)
        if v is None:
            continue
        # Enum -> str
        if hasattr(v, "name"):
            return v.name.upper()
        if hasattr(v, "value"):
            try:
                return str(v.value).upper()
            except Exception:
                return str(v)
        try:
            return str(v).upper()
        except Exception:
            pass
    return None


# Attente de "prestige" par type de restaurant : pénalités si la recette paraît "trop simple"
# Les valeurs sont multipliées (1.0 = neutre, <1 = malus)
_CONCEPT_EXPECTATION_PENALTY = {
    RestaurantType.FAST_FOOD: {
        "G5": 0.95,  # trop "haut de gamme" n'apporte pas grand-chose ici (neutre-)
        "G1": 1.00,  # très bien si frais
        "G3": 0.95,  # surgelé OK
        None: 0.98,
    },
    RestaurantType.BISTRO: {
        "G5": 0.98,  # 5ème gamme OK si bien exécuté
        "G1": 1.00,  # frais cohérent
        "G3": 0.95,  # surgelé léger malus
        None: 0.98,
    },
    RestaurantType.GASTRO: {
        "G5": 1.00,  # du sous-vide haute qualité peut être OK en gastro
        "G1": 1.00,  # frais attendu
        "G3": 0.85,  # surgelé mal vu en gastro
        None: 0.92,  # indéterminé : petit malus par prudence
    },
}


def _apply_concept_quality_adjust(restaurant: Restaurant, q: float, recipe) -> float:
    """
    Ajuste la qualité d'une recette selon les attentes du concept.
    Ex: surgelé en gastro → malus.

    Exemple
    -------
    0.765
    """
    # Extract restaurant type value, handling both enum and string cases
    restaurant_type = restaurant.type
    table = _CONCEPT_EXPECTATION_PENALTY[restaurant_type]
    hint = _recipe_grade_hint(recipe)

    # Normalise certains mots-clés
    if hint in ("FRESH", "FRAIS"):
        hint_norm = "G1"
    elif hint in ("FROZEN", "SURGELE", "SURGELÉ", "G3"):
        hint_norm = "G3"
    elif hint in ("SOUSVIDE", "SOUS_VIDE", "G5"):
        hint_norm = "G5"
    else:
        hint_norm = None

    mult = table.get(hint_norm, table.get(None, 1.0))
    return q * float(mult)


def menu_quality_mean(restaurant: Restaurant) -> float:
    """
    Calcule la qualité perçue moyenne du menu d'un restaurant.

    Cette fonction évalue la qualité globale du menu en prenant en compte :
    - La qualité intrinsèque de chaque recette
    - L'adéquation des recettes avec le concept du restaurant (ex: surgelé mal vu en gastro)
    - La satisfaction des ressources humaines (impact sur la qualité de service)

    Args:
        restaurant: L'objet Restaurant dont on veut évaluer le menu

    Returns:
        float: Score de qualité entre 0.0 et 1.0, où :
               - 0.0 = menu vide ou qualité très faible
               - 1.0 = menu de qualité excellente parfaitement adapté au concept

    """
    if not restaurant.menu:
        return 0.0

    recipe_quality_scores = []
    for recipe in restaurant.menu:
        base_quality = recipe.base_quality
        concept_adjusted_quality = _apply_concept_quality_adjust(
            restaurant, base_quality, recipe
        )
        recipe_quality_scores.append(concept_adjusted_quality)

    average_menu_quality = sum(recipe_quality_scores) / max(
        1, len(recipe_quality_scores)
    )

    # Impact de la satisfaction RH (optionnel)
    hr_satisfaction = restaurant.rh_satisfaction
    final_quality = average_menu_quality * float(hr_satisfaction)

    return final_quality


# =====================================================
# Prix & budget
# =====================================================


def price_fit(price: float, budget_moyen: float) -> float:
    """
    1.0 si <= budget; décroissance linéaire si au-dessus.

    Exemple
    -------
    1.0
    0.8
    """
    if budget_moyen <= 0:
        return 0.0
    if price <= budget_moyen:
        return 1.0
    gap = (price - budget_moyen) / budget_moyen
    val = 1.0 - max(0.0, gap)
    return val


# =====================================================
# Score d'attraction final
# =====================================================


# Matrice concept <==> segment (fit structurel)
class ConceptFitModel(BaseModel):
    FAST_FOOD: Dict[Segment, Annotated[float, Field(strict=True, ge=0, le=1)]]
    BISTRO: Dict[Segment, Annotated[float, Field(strict=True, ge=0, le=1)]]
    GASTRO: Dict[Segment, Annotated[float, Field(strict=True, ge=0, le=1)]]

    def __getitem__(self, key):
        # Allows dict-like access
        return getattr(self, key)


directory = Path("/home/lepagnol/Documents/Perso/Games/foodopsV0TL/FoodOPS_V1/data")
path = directory / "concept_fit.json"
CONCEPT_FIT = load_and_validate(path, ConceptFitModel)


class ScoreWeightsModel(BaseModel):
    fit: float  # adéquation concept <==> segment
    prix: float  # accessibilité prix vs budget
    qualite: float  # qualité perçue (recettes, RH, adéquation gamme)
    notoriete: float  # "marque", bouche-à-oreille
    visibility: float  # emplacement/visibilité du local

    def __getitem__(self, key):
        # Allows dict-like access
        return getattr(self, key)


path = directory / "scoring_weights.json"
SCORING_WEIGHTS = load_and_validate(path, ScoreWeightsModel)


def attraction_score(restaurant: Restaurant, segment_client: Segment) -> float:
    """
    Calcule un score d'attraction (entre 0.0 et 1.0) pour un restaurant et un profil client.
    Combine :
      - fit concept/segment,
      - adéquation prix vs budget,
      - qualité perçue (menu + RH + adéquation concept/gamme),
      - notoriété,
      - visibilité.
    """
    # Prix médian du menu
    menu = restaurant.menu
    prix_des_items = [item.price for item in menu if item is not None]
    price = np.median(prix_des_items) if prix_des_items else 0.0

    # Qualité moyenne perçue
    qmean = menu_quality_mean(restaurant)
    vis = restaurant.local.visibility_normalized
    notoriety = restaurant.notoriety

    # Fit concept <==> segment
    fit = CONCEPT_FIT[restaurant.type.name][segment_client]

    # Adéquation prix <==> budget segment
    budget_moyen = BUDGET_PER_SEGMENT.get(segment_client, 15.0)
    prix_ok = price_fit(price, budget_moyen)

    attrs = {
        "fit": fit,
        "prix": prix_ok,
        "qualite": qmean,
        "notoriete": notoriety,
        "visibility": vis,
    }

    score = sum(
        SCORING_WEIGHTS[key] * attrs[key] for key in SCORING_WEIGHTS.model_fields
    )

    return max(0.0, score)
