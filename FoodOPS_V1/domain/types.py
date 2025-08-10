# foodops/domain/types.py
from enum import Enum

from pydantic import BaseModel


class RestaurantType(Enum):
    # Values aligned with JSON keys and the rest of the codebase
    FAST_FOOD = "FAST_FOOD"
    BISTRO = "BISTRO"
    GASTRO = "GASTRO"


# ---------- TurnResult ----------


class TurnResult(BaseModel):
    """Snapshot des principaux KPI d'un tour pour un restaurant."""

    restaurant_name: str
    tour: int
    clients_attr: int
    clients_serv: int
    capacity: int
    price_med: float
    ca: float
    cogs: float
    fixed_costs: float
    marketing: float
    rh_cost: float
    funds_start: float
    funds_end: float
    losses: dict
