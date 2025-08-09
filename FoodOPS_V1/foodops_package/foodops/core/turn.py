# foodops/core/turn.py
# -*- coding: utf-8 -*-
"""
Mécanique de tour (allocation de la demande, capacité, prix médian du menu).
Ce module sert de façade stable pour game.py et, plus tard, pour des IA/agents.
"""

from typing import Dict, List
from ..domain import Restaurant
from .market import allocate_demand as _allocate_demand, clamp_capacity as _clamp_capacity
from ..rules.scoring import menu_price_median as _menu_price_median


def allocate_demand(restaurants: List[Restaurant], demand: int) -> Dict[int, int]:
    """
    Répartit la demande totale du tour entre restaurants selon leur score d’attraction.
    Retourne un dict {index_restaurant: clients_attribués}.
    """
    return _allocate_demand(restaurants, demand)


def clamp_capacity(restaurants: List[Restaurant], attributed: Dict[int, int]) -> Dict[int, int]:
    """
    Limite les clients attribués par la capacité de chaque restaurant sur ce tour.
    Retourne un dict {index_restaurant: clients_servis}.
    """
    return _clamp_capacity(restaurants, attributed)


def menu_price_median(r: Restaurant) -> float:
    """
    Prix médian du menu pour un restaurant (sert de proxy de panier moyen).
    """
    return _menu_price_median(r)


# —— Helpers utiles pour d’autres appels moteur (optionnels, mais propres) ——

def compute_prices_median(restaurants: List[Restaurant]) -> Dict[int, float]:
    """Retourne un dict {index_restaurant: prix_médian}."""
    return {i: _menu_price_median(r) for i, r in enumerate(restaurants)}
