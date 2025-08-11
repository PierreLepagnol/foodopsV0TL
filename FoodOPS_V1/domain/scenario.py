"""
Scénarios de population (par tour = 1 mois).
Ces données sont affichées au début et utilisées par le moteur de demande.
"""

import json
from pathlib import Path
from typing import Dict, Mapping, Optional

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """Profil de demande du marché pour un tour de jeu (1 mois)."""

    name: str
    nb_tours: int = Field(ge=1, description="Nombre de tours (1 tour = 1 mois)")
    population_total: int = Field(ge=0, description="Clients potentiels / mois")
    segments_share: Dict[str, float]
    note: str = ""


def _default_json_path() -> Path:
    return Path(__file__).with_name("scenarios.json")


def load_scenarios(json_path: Optional[Path | str] = None) -> Dict[str, Scenario]:
    """Charge les scénarios depuis le JSON et valide via Pydantic.

    Structure JSON attendue: { "code": { "name": ..., "population_total": ..., "segments_share": {...}, "note": ... }, ... }
    """

    path = Path(
        "/home/lepagnol/Documents/Perso/Games/foodopsV0TL/FoodOPS_V1/data/scenarios.json"
    )
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, Mapping):
        raise ValueError(
            "Le fichier scenarios.json doit contenir un objet JSON racine (mapping code -> scenario)."
        )

    scenarios: Dict[str, Scenario] = {}
    for code, payload in data.items():
        new_payload = {**payload, "nb_tours": 12}
        scenarios[code] = Scenario(**new_payload)
    return scenarios


CATALOG_SCENARIOS: Dict[str, Scenario] = load_scenarios()


def get_default_scenario() -> Scenario:
    """Retourne le scénario par défaut (centre-ville si disponible)."""
    if CATALOG_SCENARIOS:
        return CATALOG_SCENARIOS.get("centre_ville") or next(
            iter(CATALOG_SCENARIOS.values())
        )
    # Si rien n'est chargé (ex: fichier manquant), on renvoie un stub minimal
    return Scenario(
        name="Centre-ville mixte",
        population_total=8000,
        segments_share={
            "étudiant": 0.25,
            "actif": 0.40,
            "famille": 0.15,
            "touriste": 0.10,
            "senior": 0.10,
        },
        note="Mix équilibré, budgets variés.",
    )
