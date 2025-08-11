from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Set

from FoodOPS_V1.domain import RestaurantType


class Dept(Enum):
    CUISINE = "CUISINE"
    SALLE = "SALLE"
    SUPPORT = "SUPPORT"


class Role(Enum):
    # Cuisine
    COMMIS = "COMMIS"
    CUISINIER = "CUISINIER"
    CHEF = "CHEF"
    PLONGE = "PLONGE"
    # Salle / Caisse
    CAISSIER = "CAISSIER"
    SERVEUR = "SERVEUR"
    RUNNER = "RUNNER"
    MAITRE_D = "MAITRE_D"
    # Management
    MANAGER = "MANAGER"


# Minutes productives par heure (relative)
ROLE_PRODUCTIVITY: Dict[Role, float] = {
    Role.COMMIS: 55,  # min utiles / h
    Role.CUISINIER: 60,
    Role.CHEF: 65,
    Role.PLONGE: 45,
    Role.CAISSIER: 60,
    Role.SERVEUR: 55,
    Role.RUNNER: 60,
    Role.MAITRE_D: 45,
    Role.MANAGER: 20,  # peu de prod/service direct
}

# Affectation des rôles aux “banques” de minutes
ROLE_BANK = {
    Role.COMMIS: "prod",
    Role.CUISINIER: "prod",
    Role.CHEF: "prod",
    Role.PLONGE: "prod",  # on peut compter comme prod (soutien)
    Role.CAISSIER: "service",
    Role.SERVEUR: "service",
    Role.RUNNER: "service",
    Role.MAITRE_D: "service",
    Role.MANAGER: None,  # pas de banque directe
}

# Postes autorisés par type de resto
ALLOWED_ROLES: Dict[RestaurantType, Set[Role]] = {
    RestaurantType.FAST_FOOD: {
        Role.CUISINIER,
        Role.COMMIS,
        Role.PLONGE,
        Role.CAISSIER,
        Role.RUNNER,
        Role.MANAGER,
    },
    RestaurantType.BISTRO: {
        Role.CUISINIER,
        Role.COMMIS,
        Role.CHEF,
        Role.PLONGE,
        Role.CAISSIER,
        Role.SERVEUR,
        Role.RUNNER,
        Role.MANAGER,
    },
    RestaurantType.GASTRO: {
        Role.CUISINIER,
        Role.CHEF,
        Role.COMMIS,
        Role.PLONGE,
        Role.SERVEUR,
        Role.MAITRE_D,
        Role.RUNNER,
        Role.MANAGER,
    },
}


@dataclass
class StaffMember:
    nom: str
    role: Role
    heures_par_tour: float  # ex. 160
    salaire_total: float
