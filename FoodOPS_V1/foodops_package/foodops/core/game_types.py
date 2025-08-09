# foodops/core/game_types.py
from dataclasses import dataclass

@dataclass
class TurnResult:
    tour: int
    restaurant_name: str
    clients_attrib: int
    clients_servis: int
    prix_median: float
    ca: float
    cogs: float
    rh_cost: float
    fixed_costs: float
    marketing: float
    funds_start: float
    funds_end: float
    stock_start: float
    stock_end: float

    @staticmethod
    def from_game_state(r, tour, clients_attr, clients_serv, price_med):
        # Chiffre d'affaires
        ca = round(clients_serv * price_med, 2)

        # Coût matières (simple placeholder : 30% du CA)
        # Ici, on pourra remplacer par un vrai calcul basé sur le menu & stock
        cogs = round(ca * 0.3, 2)

        # Coût RH
        # On prend la somme des salaires totaux des employés
        rh_cost = 0.0
        if hasattr(r, "equipe") and r.equipe:
            rh_cost = sum(getattr(emp, "salaire_total", 0.0) for emp in r.equipe)

        # Charges fixes : loyer + autres charges récurrentes
        fixed_costs = r.overheads.get("loyer", 0.0) + r.overheads.get("autres", 0.0)

        # Marketing
        marketing = getattr(r, "marketing_budget", 0.0)

        # Variation de trésorerie
        funds_start = getattr(r, "funds", 0.0)
        total_costs = cogs + rh_cost + fixed_costs + marketing
        funds_end = round(funds_start + ca - total_costs, 2)

        # Stocks (placeholder — ici on ne gère pas encore les vrais mouvements)
        stock_start = getattr(r, "stock_value", 0.0)
        stock_end = stock_start  # à ajuster si variation réelle

        return TurnResult(
            tour=tour,
            restaurant_name=r.name,
            clients_attrib=clients_attr,
            clients_servis=clients_serv,
            prix_median=price_med,
            ca=ca,
            cogs=cogs,
            rh_cost=rh_cost,
            fixed_costs=fixed_costs,
            marketing=marketing,
            funds_start=funds_start,
            funds_end=funds_end,
            stock_start=stock_start,
            stock_end=stock_end
        )