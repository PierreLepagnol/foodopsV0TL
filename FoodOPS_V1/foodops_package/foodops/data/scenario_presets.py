# -*- coding: utf-8 -*-
"""
Scénarios de population (par tour = 1 mois).
Ces données sont affichées au début et utilisées par le moteur de demande.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Scenario:
    name: str
    population_total: int                # clients potentiels / mois
    segments_share: Dict[str, float]     # clés: "étudiant","actif","famille","touriste","senior"
    note: str = ""


# Quelques profils prêts à l’emploi (tu peux en ajouter d’autres)
SCENARIOS: Dict[str, Scenario] = {
    "quartier_etudiant": Scenario(
        name="Quartier étudiant animé",
        population_total=5000,
        segments_share={
            "étudiant": 0.60,
            "actif": 0.20,
            "famille": 0.10,
            "touriste": 0.05,
            "senior": 0.05,
        },
        note="Fort volume midi, sensibilité prix élevée."
    ),
    "centre_ville": Scenario(
        name="Centre-ville mixte",
        population_total=8000,
        segments_share={
            "étudiant": 0.25,
            "actif": 0.40,
            "famille": 0.15,
            "touriste": 0.10,
            "senior": 0.10,
        },
        note="Mix équilibré, budgets variés."
    ),
    "zone_touristique": Scenario(
        name="Zone touristique",
        population_total=7000,
        segments_share={
            "étudiant": 0.10,
            "actif": 0.25,
            "famille": 0.15,
            "touriste": 0.40,
            "senior": 0.10,
        },
        note="Forte attente expérience/qualité, sensibilité moindre au prix."
    ),
}


def get_default_scenario() -> Scenario:
    # Choix par défaut si non configuré : centre-ville
    return SCENARIOS["centre_ville"]
