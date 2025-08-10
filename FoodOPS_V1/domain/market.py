"""
Domain market primitives: customer segments and budgets.

This module defines the Segment enum and the average budget per segment.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Dict


def load_segment_data() -> Dict[str, Dict[str, float | str]]:
    """Load segment data from segment_clients.json file."""
    data_path = Path(__file__).parent.parent / "data" / "segment_clients.json"
    with data_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# Load segment data from JSON
_SEGMENT_DATA = load_segment_data()


class Segment(str, Enum):
    """Segments de clientèle (valeurs textuelles alignées avec les données/scoring)."""

    ETUDIANT = "etudiant"
    ACTIF = "actif"
    FAMILLE = "famille"
    TOURISTE = "touriste"
    SENIOR = "senior"


# Extract budgets from loaded data
BUDGET_PER_SEGMENT: Dict[Segment, float] = {
    Segment(key): float(data["budget_moyen"])
    for key, data in _SEGMENT_DATA.items()
    if key in [segment.value for segment in Segment]
}


__all__ = ["Segment", "BUDGET_PER_SEGMENT"]
