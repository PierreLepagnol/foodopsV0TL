from dataclasses import dataclass
from .game_types import TurnResult
from ..rules.costing import compute_average_unit_cogs

def compute_turn_result(r, tour, clients_attrib, clients_servis, prix_median):
    """
    Calcule tous les résultats financiers d'un tour pour un restaurant.
    Utilise les prix matière réels des recettes.
    """
    # Chiffre d'affaires
    ca = clients_servis * prix_median

    # --- COGS (coût matière réel) ---
    if r.menu:
        unit = compute_average_unit_cogs(r.menu)
        cogs = round(unit * clients_servis, 2)
    else:
        cogs = 0.0


    # Charges fixes (loyer, abonnements, etc.)
    fixed_costs = r.overheads.get("loyer", 0.0) + r.overheads.get("autres", 0.0)

    # Budget marketing
    marketing = getattr(r, "marketing_budget", 0.0)

    # Charges RH
    rh_cost = sum(emp.salaire_total for emp in getattr(r, "employes", [])) if hasattr(r, "employes") else 0.0

    # Trésorerie début
    funds_start = getattr(r, "funds", 0.0)

    # Trésorerie fin (hors remboursements d'emprunt, gérés séparément)
    funds_end = funds_start + ca - cogs - fixed_costs - marketing - rh_cost

    # Retourne l'objet standardisé
    return TurnResult(
        tour=tour,
        restaurant=r.name,
        clients_attrib=clients_attrib,
        clients_servis=clients_servis,
        prix_median=prix_median,
        ca=ca,
        cogs=cogs,
        fixed_costs=fixed_costs,
        marketing=marketing,
        rh_cost=rh_cost,
        funds_start=funds_start,
        funds_end=funds_end
    )
