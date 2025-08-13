"""
Scénarios de population (par tour = 1 mois).
Ces données sont affichées au début et utilisées par le moteur de demande.
"""

import json
from pathlib import Path
from typing import Dict, Mapping, Optional

from pydantic import BaseModel, Field

from FoodOPS_V1.domain.market import Segment


class Scenario(BaseModel):
    """
    Profil de demande du marché pour un tour de jeu (1 mois).

    Exemple de scénario:
    {
    "quartier_etudiant": {
        "name": "Quartier étudiant animé",
        "population_total": 5000,
        "segments_share": {
            Segment.ETUDIANT: 0.6,
            Segment.ACTIF: 0.2,
            Segment.FAMILLE: 0.1,
            Segment.TOURISTE: 0.05,
            Segment.SENIOR: 0.05
        },
        "note": "Fort volume midi, sensibilité prix élevée."
    }
    """

    name: str
    nb_tours: int = Field(ge=1, description="Nombre de tours (1 tour = 1 mois)")
    population_total: int = Field(ge=0, description="Clients potentiels / mois")
    segments_share: Dict[Segment, float]
    note: str = ""

    def show_scenario(self) -> None:
        print(f"📍 Scénario : {self.name}")
        population_total = self.population_total
        population_total = f"{population_total:,}".replace(",", " ")
        if self.note:
            print(f"📝 {self.note}")
        print(f"👥 Population totale potentielle (mois) : {population_total}")
        print("🔎 Répartition :")
        for k in ("étudiant", "actif", "famille", "touriste", "senior"):
            share = self.segments_share[k]
            print(f"- {k.capitalize():9s} : {int(share * 100)}%")

    def compute_segment_quantities(self) -> Dict[Segment, int]:
        """Convertit les parts du scénario en volumes entiers par segment."""
        demand = {
            segment: int(round(self.population_total * share))
            for segment, share in self.segments_share.items()
        }
        return demand


def load_scenarios(json_path: Optional[Path | str] = None) -> Dict[str, Scenario]:
    """Charge les scénarios depuis le JSON et valide via Pydantic.

    Structure JSON attendue: { "code": { "name": ..., "population_total": ..., "segments_share": {...}, "note": ... }, ... }
    """

    path = Path(json_path)
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


path = "/home/lepagnol/Documents/Perso/Games/foodopsV0TL/FoodOPS_V1/data/scenarios.json"
CATALOG_SCENARIOS: Dict[str, Scenario] = load_scenarios(path)


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
            Segment.ETUDIANT: 0.25,
            Segment.ACTIF: 0.40,
            Segment.FAMILLE: 0.15,
            Segment.TOURISTE: 0.10,
            Segment.SENIOR: 0.10,
        },
        note="Mix équilibré, budgets variés.",
    )
