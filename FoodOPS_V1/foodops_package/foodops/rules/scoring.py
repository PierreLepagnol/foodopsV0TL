# foodops/rules/scoring.py
from typing import Dict
from statistics import median
from ..data.profiles import ProfilClient
from ..domain.restaurant import Restaurant

SCORING_WEIGHTS: Dict[str, float] = {
    "fit": 0.25,
    "prix": 0.25,
    "qualite": 0.25,
    "notoriete": 0.15,
    "visibilite": 0.10,
}

def _median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return 0.5 * (s[mid - 1] + s[mid])

def menu_price_median(resto: Restaurant) -> float:
    """
    Calcule le prix médian du menu en utilisant suggest_price()
    + plancher anti-dumping à 102% du COGS estimé
    + markup global (resto.pricing_markup).
    """
    if not getattr(resto, "menu", None):
        return 0.0

    prices = []
    markup = getattr(resto, "pricing_markup", 0.0)

    for recipe in resto.menu:
        try:
            cogs = float(recipe.cogs())
        except Exception:
            cogs = float(getattr(recipe, "base_cost", 0.0))

        try:
            p = float(recipe.suggest_price())
        except Exception:
            p = cogs * 1.7 if cogs > 0 else 12.0

        p *= (1.0 + markup)
        p = max(p, cogs * 1.02)  # anti-dumping
        prices.append(p)

    return float(median(prices)) if prices else 0.0

def menu_quality_mean(resto: Restaurant) -> float:
    if not resto.menu:
        return 0.0
    return sum(getattr(r, "base_quality", 0.0) for r in resto.menu) / len(resto.menu)

def price_fit(price: float, budget_moyen: float) -> float:
    if budget_moyen <= 0:
        return 0.0
    if price <= budget_moyen:
        return 1.0
    gap = (price - budget_moyen) / budget_moyen
    val = 1.0 - max(0.0, gap)
    return max(0.0, min(1.0, val))

def attraction_score(resto: Restaurant, seg: ProfilClient) -> float:
    price = menu_price_median(resto)
    qmean = menu_quality_mean(resto)
    # ⚠️ important : le champ s’appelle visibilite dans Local
    vis = min(1.0, max(0.0, getattr(resto.local, "visibilite", 1.0) / 5.0))

    # Fit concept vs segment — V1 simple
    concept_fit_matrix = {
        "Fast Food":      {"étudiant":0.9, "actif":0.6, "famille":0.6, "touriste":0.5, "senior":0.4},
        "Bistrot":        {"étudiant":0.6, "actif":0.8, "famille":0.75,"touriste":0.7, "senior":0.7},
        "Gastronomique":  {"étudiant":0.3, "actif":0.6, "famille":0.7, "touriste":0.85,"senior":0.8},
    }
    fit = concept_fit_matrix.get(resto.type.value, {}).get(seg.type_client.value, 0.6)
    attrs = {
        "fit": fit,
        "prix": price_fit(price, seg.budget_moyen),
        "qualite": max(0.0, min(1.0, qmean)),
        "notoriete": max(0.0, min(1.0, resto.notoriety)),
        "visibilite": vis,
    }
    w = SCORING_WEIGHTS
    return sum(w[k] * attrs.get(k, 0.0) for k in w.keys())
