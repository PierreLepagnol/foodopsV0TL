# -*- coding: utf-8 -*-
"""
Moteur d'allocation de la demande (réaliste) pour FoodOps.

Règles implémentées :
- La demande vient d’un Scenario (population totale + parts par segments).
- Choix d’un restaurant (pas d’un “type” abstrait) en fonction d’un score d’attraction.
- Filtre budget dur : si prix médian du resto > budget segment × tolérance => resto inéligible.
- Capacité exploitable par tour = capacité brute × coefficient de vitesse (par type de resto).
- Redistribution en cas de saturation : on passe au 2e, 3e meilleur, etc.
- Clients perdus si aucun resto éligible ou plus de capacité.
- Cannibalisation douce : si plusieurs restos d’un même type, légère pénalité de score.

Retour :
    allocate_demand(...) -> dict {index_restaurant: clients_attribués}

NB : Les clients “perdus” ne sont pas retournés ici, mais on expose
     une fonction optionnelle `estimate_lost_customers(...)` si besoin plus tard.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from math import sqrt

from ..domain import Restaurant, RestaurantType
from ..rules.scoring import attraction_score, menu_price_median
from ..data.scenario_presets import Scenario

# ------------------------------
# Paramètres “marché” (ajustables)
# ------------------------------

# Vitesse de service => % de capacité exploitable sur le mois
SERVICE_SPEED: Dict[RestaurantType, float] = {
    RestaurantType.FAST_FOOD: 1.00,  # service rapide
    RestaurantType.BISTRO:    0.80,  # table servie
    RestaurantType.GASTRO:    0.50,  # repas long
}

# Budgets moyens (panier) par segment (à affiner si besoin)
SEGMENT_BUDGET: Dict[str, float] = {
    "étudiant": 10.0,
    "actif":    18.0,
    "famille":  55.0,   # panier pour 3-4
    "touriste": 28.0,
    "senior":   20.0,
}

# Tolérance budget (ex: 1.20 => 20% au-dessus du budget moyen toléré)
BUDGET_TOLERANCE: float = 1.20

# Pénalité “cannibalisation” : plus il y a de restos d’un même type, plus on pénalise légèrement le score.
# Ex: factor = 1 / sqrt(1 + alpha*(n_same_type-1))
CANNI_ALPHA: float = 0.50


# ------------------------------
# Petits shims & helpers
# ------------------------------

@dataclass(frozen=True)
class _SegShim:
    """Shim minimal pour réutiliser attraction_score(resto, ProfilClient-like)."""
    type_client: object
    budget_moyen: float

@dataclass(frozen=True)
class _TypeShim:
    value: str


def _cap_exploitable(resto: Restaurant) -> int:
    """
    Capacité mensuelle exploitable = local.capacite_clients * 2 services * 30 jours * coef vitesse.
    """
    base = resto.local.capacite_clients * 2 * 30
    coef = SERVICE_SPEED.get(resto.type, 1.0)
    return max(0, int(base * coef))


def _eligible_by_budget(resto: Restaurant, segment: str) -> bool:
    price = menu_price_median(resto)
    budget = SEGMENT_BUDGET.get(segment, 15.0)
    return price <= budget * BUDGET_TOLERANCE


def _count_by_type(restos: List[Restaurant]) -> Dict[RestaurantType, int]:
    counts: Dict[RestaurantType, int] = {}
    for r in restos:
        counts[r.type] = counts.get(r.type, 0) + 1
    return counts


def _cannibalization_factor(resto: Restaurant, counts_by_type: Dict[RestaurantType, int]) -> float:
    n = counts_by_type.get(resto.type, 1)
    if n <= 1:
        return 1.0
    # plus n est grand, plus on réduit le score (faiblement)
    return 1.0 / max(1.0, sqrt(1.0 + CANNI_ALPHA * (n - 1)))


def _segment_quantities(sc: Scenario) -> Dict[str, int]:
    demand: Dict[str, int] = {}
    for seg, share in sc.segments_share.items():
        demand[seg] = int(round(sc.population_total * share))
    return demand


def _ranked_for_segment(
    restos: List[Restaurant],
    segment: str,
    counts_by_type: Dict[RestaurantType, int]
) -> List[Tuple[int, float]]:
    """
    Classement (idx, score) décroissant pour un segment donné, en filtrant hors budget
    et en appliquant la pénalité de cannibalisation.
    """
    ranked: List[Tuple[int, float]] = []
    for idx, r in enumerate(restos):
        if not _eligible_by_budget(r, segment):
            continue
        # Shim ProfilClient-like
        seg_obj = _SegShim(type_client=_TypeShim(value=segment), budget_moyen=SEGMENT_BUDGET.get(segment, 15.0))
        base_score = max(0.0, attraction_score(r, seg_obj))
        penal = _cannibalization_factor(r, counts_by_type)
        ranked.append((idx, base_score * penal))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


# ------------------------------
# API principale
# ------------------------------

def allocate_demand(restaurants: List[Restaurant], scenario: Scenario) -> Dict[int, int]:
    """
    Allocation segmentée + filtrage budget + saturation + redistribution.
    Retourne : {index_restaurant: clients_attribués}
    """
    demand_by_seg = _segment_quantities(scenario)
    counts_by_type = _count_by_type(restaurants)

    # Capacité exploitable restante par resto
    capacity_left: Dict[int, int] = {i: _cap_exploitable(r) for i, r in enumerate(restaurants)}
    allocated: Dict[int, int] = {i: 0 for i in range(len(restaurants))}

    for seg, qty in demand_by_seg.items():
        if qty <= 0:
            continue

        ranked = _ranked_for_segment(restaurants, seg, counts_by_type)

        # Si aucun resto éligible au budget de ce segment → tout perdu
        if not ranked:
            continue

        remaining = qty

        # Attribution gloutonne : on remplit le meilleur, puis le suivant s'il est plein, etc.
        for idx, _score in ranked:
            if remaining <= 0:
                break
            if capacity_left[idx] <= 0:
                continue
            take = min(remaining, capacity_left[idx])
            allocated[idx] += take
            capacity_left[idx] -= take
            remaining -= take

        # remainder (= clients perdus) : on ne le stocke pas ici ; à afficher ailleurs si besoin

    return allocated


def clamp_capacity(restaurants: List[Restaurant], allocated: Dict[int, int]) -> Dict[int, int]:
    """
    Par sécurité — borne par capacité exploitable si des couches supérieures
    modifient les quantités entre-temps.
    """
    served: Dict[int, int] = {}
    for i, r in enumerate(restaurants):
        cap = _cap_exploitable(r)
        served[i] = min(allocated.get(i, 0), cap)
    return served


# ------------------------------
# Outils optionnels (debug/stats)
# ------------------------------

def estimate_lost_customers(restaurants: List[Restaurant], scenario: Scenario) -> int:
    """
    Renvoie une estimation des clients perdus si on réapplique l’algorithme (utile debug).
    NOTE: non utilisé par le jeu, juste pour instrumentation future.
    """
    demand_by_seg = _segment_quantities(scenario)
    counts_by_type = _count_by_type(restaurants)
    capacity_left: Dict[int, int] = {i: _cap_exploitable(r) for i, r in enumerate(restaurants)}
    lost_total = 0

    for seg, qty in demand_by_seg.items():
        remaining = qty
        ranked = _ranked_for_segment(restaurants, seg, counts_by_type)
        if not ranked:
            lost_total += remaining
            continue
        for idx, _score in ranked:
            if remaining <= 0:
                break
            if capacity_left[idx] <= 0:
                continue
            take = min(remaining, capacity_left[idx])
            capacity_left[idx] -= take
            remaining -= take
        lost_total += remaining

    return lost_total
