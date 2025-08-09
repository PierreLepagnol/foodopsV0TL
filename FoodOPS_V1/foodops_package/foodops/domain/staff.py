
# -*- coding: utf-8 -*-
"""Gestion du personnel / staff."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
from enum import Enum, auto

# IMPORTANT : pas d'import du package domain complet ici (pour éviter les cycles)
# Si tu dois typer Restaurant ailleurs, fais-le avec TYPE_CHECKING dans ce fichier-là.

class Role(Enum):
    SERVEUR = auto()
    CUISINIER = auto()
    MANAGER = auto()

# Pour les endroits du code qui faisaient référence à “ALLOWED_ROLES”
ALLOWED_ROLES = {Role.SERVEUR, Role.CUISINIER, Role.MANAGER}

# Productivité “minutes par tour” de base par rôle
# (8h * 60min = 480min ; le manager file un coup de main léger aux deux)
ROLE_PRODUCTIVITY: Dict[Role, Dict[str, int]] = {
    Role.SERVEUR:  {"service_minutes": 480, "kitchen_minutes": 0},
    Role.CUISINIER:{"service_minutes": 0,   "kitchen_minutes": 480},
    Role.MANAGER:  {"service_minutes": 120, "kitchen_minutes": 120},
}

# Certains modules faisaient allusion à ROLE_BANK — on l’expose “vide” pour compat,
# ou catégorisation front/back si tu veux t’en servir plus tard.
ROLE_BANK: Dict[Role, str] = {
    Role.SERVEUR:  "front",
    Role.CUISINIER:"back",
    Role.MANAGER:  "both",
}

@dataclass
class Employe:
    nom: str
    role: Role
    salaire_total: float = 0.0        # coût total mensuel/“tour”
    productivite_bonus: float = 1.0   # multiplicateur (ex : 1.1 = +10%)
    present: bool = True              # si absent/malade …

    # Etats calculés (optionnels)
    service_minutes: int = field(default=0, init=False)
    kitchen_minutes: int = field(default=0, init=False)

    def compute_minutes(self) -> None:
        """Calcule les minutes dispo pour ce tour selon le rôle et le bonus."""
        base = ROLE_PRODUCTIVITY.get(self.role, {"service_minutes": 0, "kitchen_minutes": 0})
        if not self.present:
            self.service_minutes = 0
            self.kitchen_minutes = 0
            return
        sm = int(base["service_minutes"] * float(self.productivite_bonus))
        km = int(base["kitchen_minutes"] * float(self.productivite_bonus))
        self.service_minutes = max(0, sm)
        self.kitchen_minutes = max(0, km)
