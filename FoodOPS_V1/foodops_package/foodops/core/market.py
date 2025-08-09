# foodops/core/market.py
# -*- coding: utf-8 -*-
from typing import Dict, List
from ..domain import Restaurant
from ..rules.scoring import attraction_score, menu_price_median
from ..data import get_CLIENT_PROFILES, get_SEGMENT_WEIGHTS

def _attractions_by_segment(restaurants: List[Restaurant]) -> Dict[str, List[float]]:
    """
    Retourne, pour chaque segment, la liste des attractions par restaurant.
    """
    profiles = get_CLIENT_PROFILES()
    result: Dict[str, List[float]] = {}
    for seg_key, seg in profiles.items():
        arr = []
        for r in restaurants:
            arr.append(attraction_score(r, seg))
        result[seg_key] = arr
    return result

def allocate_demand(restaurants: List[Restaurant], total_demand: int) -> Dict[int, int]:
    """
    Répartit la demande totale entre restaurants en fonction de l’attraction par segment.
    """
    segment_weights = get_SEGMENT_WEIGHTS()
    profiles = get_CLIENT_PROFILES()

    # Demande par segment (arrondie)
    demand_by_seg = {seg: int(round(total_demand * weight)) for seg, weight in segment_weights.items()}

    # Attraction par segment
    attr_seg = _attractions_by_segment(restaurants)

    attributed = {i: 0 for i in range(len(restaurants))}
    for seg, seg_demand in demand_by_seg.items():
        vec = attr_seg.get(seg, [])
        if not vec:
            continue
        total_attr = sum(a for a in vec if a > 0)
        if total_attr <= 0:
            continue
        for i, a in enumerate(vec):
            if a <= 0:
                continue
            attributed[i] += int(round(seg_demand * (a / total_attr)))

    return attributed

def clamp_capacity(restaurants: List[Restaurant], attributed: Dict[int, int]) -> Dict[int, int]:
    """
    Limite les clients attribués par la capacité mensuelle de chaque restaurant.
    """
    served: Dict[int, int] = {}
    for i, r in enumerate(restaurants):
        cap = r.capacity_per_turn
        served[i] = min(max(0, attributed.get(i, 0)), cap)
    return served
