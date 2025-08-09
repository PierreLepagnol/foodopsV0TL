# -*- coding: utf-8 -*-
from .console_style import cyan, bold  # si tu n'as pas console_style, remplace par print simple
from ..data.scenario_presets import Scenario

def show_scenario(sc: Scenario) -> None:
    print()
    print(bold(f"📍 Scénario : {sc.name}"))
    if sc.note:
        print(f"📝 {sc.note}")
    print(f"👥 Population totale potentielle (mois) : {sc.population_total:,}".replace(",", " "))
    print("🔎 Répartition :")
    for k in ("étudiant", "actif", "famille", "touriste", "senior"):
        share = sc.segments_share.get(k, 0.0)
        print(f"  - {k.capitalize():9s} : {int(share*100)}%")
    print()
