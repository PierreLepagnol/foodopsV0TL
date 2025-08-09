# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class ProfilClient:
    label: str
    budget_min: float
    budget_max: float
    importance_prix: float
    importance_qualite: float
    importance_rapidite: float
    importance_service: float

# Profils (simplifiés) — pour gameplay
CLIENT_PROFILES: Dict[str, ProfilClient] = {
    "ETUDIANT": ProfilClient(
        label="Étudiant",
        budget_min=6.0,
        budget_max=14.0,
        importance_prix=0.50,
        importance_qualite=0.20,
        importance_rapidite=0.25,
        importance_service=0.05,
    ),
    "ACTIF": ProfilClient(
        label="Actif",
        budget_min=12.0,
        budget_max=25.0,
        importance_prix=0.25,
        importance_qualite=0.35,
        importance_rapidite=0.30,
        importance_service=0.10,
    ),
    "TOURISTE": ProfilClient(
        label="Touriste",
        budget_min=15.0,
        budget_max=45.0,
        importance_prix=0.15,
        importance_qualite=0.45,
        importance_rapidite=0.15,
        importance_service=0.25,
    ),
    "FAMILLE": ProfilClient(
        label="Famille",
        budget_min=40.0,  # ticket de table
        budget_max=80.0,
        importance_prix=0.30,
        importance_qualite=0.30,
        importance_rapidite=0.25,
        importance_service=0.15,
    ),
    "SENIOR": ProfilClient(
        label="Senior",
        budget_min=15.0,
        budget_max=30.0,
        importance_prix=0.20,
        importance_qualite=0.40,
        importance_rapidite=0.10,
        importance_service=0.30,
    ),
}

# Pondération des segments (ex: campus = +étudiants)
SEGMENT_WEIGHTS: Dict[str, float] = {
    "ETUDIANT": 0.45,
    "ACTIF":    0.30,
    "TOURISTE": 0.10,
    "FAMILLE":  0.10,
    "SENIOR":   0.05,
}
