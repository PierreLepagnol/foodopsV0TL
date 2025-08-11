from typing import Dict, List, Optional

import numpy as np

from FoodOPS_V1.data.profiles import ProfilClient
from FoodOPS_V1.domain import Restaurant

# class RestaurantType:  # fallback minimal
#     FAST_FOOD = type("E", (), {"value": "Fast Food"})
#     BISTRO = type("E", (), {"value": "Bistrot"})
#     GASTRO = type("E", (), {"value": "Gastronomique"})


# ==========================
# Poids des critères (somme ~ 1)
# ==========================
SCORING_WEIGHTS: Dict[str, float] = {
    "fit": 0.25,  # adéquation concept <==> segment
    "prix": 0.25,  # accessibilité prix vs budget
    "qualite": 0.25,  # qualité perçue (recettes, RH, adéquation gamme)
    "notoriete": 0.15,  # “marque”, bouche-à-oreille
    "visibilite": 0.10,  # emplacement/visibilité du local
}

# ==========================
# Petits helpers génériques
# ==========================


def _clamp01(x: float) -> float:
    """Borne une valeur dans [0,1].

    Exemple
    -------
    >>> _clamp01(-5)
    0.0
    >>> _clamp01(0.3)
    0.3
    >>> _clamp01(99)
    1.0
    """
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


# =====================================================
# Qualité perçue du menu
#  - Combine la qualité des recettes (moyenne)
#  - Applique un ajustement “exigence du concept”
#  - Applique la satisfaction RH (optionnelle)
# =====================================================


def _recipe_quality_base(recipe) -> float:
    """
    Essaye plusieurs noms de champs usuels pour la qualité intrinsèque d'une recette.
    Valeur attendue dans [0..1]. Par défaut 0.6 (correct).

    Exemple
    -------
    >>> class R: pass
    >>> r = R(); r.base_quality = 0.8
    >>> _recipe_quality_base(r)
    0.8
    >>> r2 = R(); r2.quality = 2.0  # bornée
    >>> _recipe_quality_base(r2)
    1.0
    """
    for attr in ("quality", "base_quality", "quality_base", "q_base"):
        val = getattr(recipe, attr, None)
        if val is not None:
            try:
                return _clamp01(float(val))
            except Exception:
                pass
    return 0.60


def _recipe_grade_hint(recipe) -> Optional[str]:
    """
    Retourne un hint de “gamme ingrédient” si disponible.
    Ex. 'G1','G3','G5' ou 'fresh','frozen','sousvide'. None si indéterminé.

    Exemple
    -------
    >>> class R: pass
    >>> r = R(); r.grade_hint = 'g3'
    >>> _recipe_grade_hint(r)
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


# Attente de “prestige” par type de restaurant : pénalités si la recette paraît “trop simple”
# Les valeurs sont multipliées (1.0 = neutre, <1 = malus)
_CONCEPT_EXPECTATION_PENALTY = {
    "Fast Food": {
        "G5": 0.95,  # trop “haut de gamme” n'apporte pas grand-chose ici (neutre-)
        "G1": 1.00,  # très bien si frais
        "G3": 0.95,  # surgelé OK
        None: 0.98,
    },
    "Bistrot": {
        "G5": 0.98,  # 5ème gamme OK si bien exécuté
        "G1": 1.00,  # frais cohérent
        "G3": 0.95,  # surgelé léger malus
        None: 0.98,
    },
    "Gastronomique": {
        "G5": 1.00,  # du sous-vide haute qualité peut être OK en gastro
        "G1": 1.00,  # frais attendu
        "G3": 0.85,  # surgelé mal vu en gastro
        None: 0.92,  # indéterminé : petit malus par prudence
    },
}


def _apply_concept_quality_adjust(resto: Restaurant, q: float, recipe) -> float:
    """
    Ajuste la qualité d'une recette selon les attentes du concept.
    Ex: surgelé en gastro → malus.

    Exemple
    -------
    >>> class R: pass
    >>> resto = R(); resto.type = type('T', (), {'value': 'Gastronomique'})
    >>> class X: pass
    >>> x = X(); x.grade_hint='G3'
    >>> _apply_concept_quality_adjust(resto, 0.9, x)
    0.765
    """
    concept = getattr(getattr(resto, "type", None), "value", None) or getattr(
        resto, "type", "Bistrot"
    )
    concept = str(concept)
    table = _CONCEPT_EXPECTATION_PENALTY.get(
        concept, _CONCEPT_EXPECTATION_PENALTY["Bistrot"]
    )
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
    return _clamp01(q * float(mult))


def menu_quality_mean(resto: Restaurant) -> float:
    """
    Qualité perçue moyenne du menu (0..1), ajustée par concept et satisfaction RH.

    Exemple
    -------
    >>> class R: pass
    >>> resto = R(); resto.type = type('T', (), {'value': 'Bistrot'}); resto.menu=[]
    >>> menu_quality_mean(resto)
    0.0
    """
    menu = getattr(resto, "menu", None) or []
    if not menu:
        return 0.0

    qualities = []
    for it in menu:
        q = _recipe_quality_base(it)
        q = _apply_concept_quality_adjust(resto, q, it)
        qualities.append(q)

    qmean = sum(qualities) / max(1, len(qualities))

    # Impact satisfaction RH (optionnel)
    rh_sat = getattr(resto, "rh_satisfaction", None)
    if rh_sat is not None:
        qmean = _clamp01(qmean * _clamp01(float(rh_sat)))

    return qmean


# =====================================================
# Prix & budget
# =====================================================


def price_fit(price: float, budget_moyen: float) -> float:
    """
    1.0 si <= budget; décroissance linéaire si au-dessus.

    Exemple
    -------
    >>> price_fit(10, 10)
    1.0
    >>> price_fit(12, 10)
    0.8
    """
    if budget_moyen <= 0:
        return 0.0
    if price <= budget_moyen:
        return 1.0
    gap = (price - budget_moyen) / budget_moyen
    val = 1.0 - max(0.0, gap)
    return _clamp01(val)


# =====================================================
# Score d'attraction final
# =====================================================

# Matrice concept <==> segment (fit structurel)
_CONCEPT_FIT = {
    "Fast Food": {
        "étudiant": 0.90,
        "actif": 0.60,
        "famille": 0.60,
        "touriste": 0.50,
        "senior": 0.40,
    },
    "Bistrot": {
        "étudiant": 0.60,
        "actif": 0.80,
        "famille": 0.75,
        "touriste": 0.70,
        "senior": 0.70,
    },
    "Gastronomique": {
        "étudiant": 0.30,
        "actif": 0.60,
        "famille": 0.70,
        "touriste": 0.85,
        "senior": 0.80,
    },
}


def _visibility_norm(resto: Restaurant) -> float:
    """
    Normalise la visibilité du local en [0..1].
    On suppose local.visibility ~ 0..5 (adapter si autre échelle).

    Exemple
    -------
    >>> class L: pass
    >>> class R: pass
    >>> l=L(); l.visibility=5; r=R(); r.local=l
    >>> _visibility_norm(r)
    1.0
    """
    local = getattr(resto, "local", None)
    vis = getattr(local, "visibility", None)
    if vis is None:
        return 0.5
    try:
        return _clamp01(float(vis) / 5.0)
    except Exception:
        return 0.5


def attraction_score(resto: Restaurant, seg: ProfilClient) -> float:
    """
    Calcule un score d'attraction (0..1) pour un restaurant et un profil client.
    Combine :
      - fit concept/segment,
      - adéquation prix vs budget,
      - qualité perçue (menu + RH + adéquation concept/gamme),
      - notoriété,
      - visibilité.

    Exemple
    -------
    >>> class R: pass
    >>> resto = R(); resto.type = type('T', (), {'value': 'Bistrot'}); resto.menu=[]; resto.local=type('L', (), {'visibility':3})
    >>> class S: pass
    >>> seg = S(); seg.type_client = type('K', (), {'name':'actif'}); seg.budget_moyen=15
    >>> 0.0 <= attraction_score(resto, seg) <= 1.0
    True
    """
    # Prix médian du menu
    menu = resto.menu if hasattr(resto, "menu") else []
    prix_des_items = [item.price for item in menu if item is not None]
    price = np.median(prix_des_items) if prix_des_items else 0.0

    # Qualité moyenne perçue
    qmean = menu_quality_mean(resto)
    # Visibilité normalisée
    vis = _visibility_norm(resto)
    # Notoriété bornée
    notoriety = _clamp01(float(getattr(resto, "notoriety", 0.5)))

    # Fit concept <==> segment
    concept = getattr(getattr(resto, "type", None), "value", None) or getattr(
        resto, "type", "Bistrot"
    )
    concept = str(concept)
    # seg_key = getattr(seg, "type_client", None)
    seg_key = seg.type_client
    seg_key = (
        getattr(seg_key, "value", None)
        or getattr(seg_key, "name", None)
        or str(seg_key)
        or "actif"
    )
    fit = _CONCEPT_FIT.get(concept, _CONCEPT_FIT["Bistrot"]).get(seg_key, 0.6)

    # Adéquation prix <==> budget segment
    budget_moyen = float(getattr(seg, "budget_moyen", 0.0) or 0.0)
    prix_ok = price_fit(price, budget_moyen)

    attrs = {
        "fit": fit,
        "prix": prix_ok,
        "qualite": qmean,
        "notoriete": notoriety,
        "visibilite": vis,
    }

    w = SCORING_WEIGHTS
    score = (
        w["fit"] * attrs["fit"]
        + w["prix"] * attrs["prix"]
        + w["qualite"] * attrs["qualite"]
        + w["notoriete"] * attrs["notoriete"]
        + w["visibilite"] * attrs["visibilite"]
    )

    # Garde bien le score borné
    return _clamp01(score)
