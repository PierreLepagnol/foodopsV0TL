"""
Moteur RH : calcul coûts, capacités, satisfaction, et gestion contrats.
"""

import json
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel


class RestaurantRoleStats(BaseModel):
    salaire_marche: int
    capacite_couverts: int
    impact_qualite: float


class Role(BaseModel):
    nom: str
    categorie: str
    restaurant_types: Dict[str, RestaurantRoleStats]


def load_roles_from_json(json_path: Path) -> List[Role]:
    """
    Load roles from the JSON file and return as a list of Role objects.
    """
    with open(json_path, "r", encoding="utf-8") as file:
        roles_data = json.load(file)

    return [Role(**role_data) for role_data in roles_data]


CHARGES_PATRONALES = 0.42  # 42% charges patronales
COUT_LICENCIEMENT_MOIS = 1  # 1 mois de salaire brut
COUT_EMBAUCHE_FIXE = 400  # coût comptable / administratif

path = Path(
    "/home/lepagnol/Documents/Perso/Games/foodopsV0TL/FoodOPS_V1/data/roles.json"
)
ROLES = load_roles_from_json(path)
PRENOMS = [
    "Alex",
    "Marie",
    "Lucas",
    "Sophie",
    "Karim",
    "Claire",
    "Hugo",
    "Lea",
    "Antoine",
    "Nadia",
]
NOMS = [
    "Durand",
    "Moreau",
    "Lefevre",
    "Garcia",
    "Bernard",
    "Petit",
    "Roux",
    "Fontaine",
]


def calcul_capacite_totale(equipe, type_resto):
    """
    Additionne les capacités couverts/tour selon les rôles.
    """
    base_roles = {r["nom"]: r for r in ROLES[type_resto]}
    capacite = 0
    for employe in equipe:
        role = base_roles.get(employe["nom"])
        if role:
            capacite += role["capacite_couverts"]
    return capacite


def cout_licenciement(employe):
    """
    Calcule le coût de licenciement d'un employé.
    """
    return employe["salaire"] * COUT_LICENCIEMENT_MOIS
