from dataclasses import dataclass, field
from enum import Enum
from typing import List, TYPE_CHECKING
from .local import Local

if TYPE_CHECKING:
    from .recipe import Recipe  # uniquement pour les hints, pas à l’exécution

class RestaurantType(Enum):
    FAST_FOOD = "Fast Food"
    BISTRO = "Bistrot"
    GASTRO = "Gastronomique"

@dataclass
class Restaurant:
    # --- Obligatoires (sans défaut) : d'abord ! ---
    name: str
    type: RestaurantType
    local: Local
    funds: float
    equipment_invest: float

    # --- Jeu / offre ---
    menu: List["Recipe"] = field(default_factory=list)
    notoriety: float = 0.5  # neutre

    # --- Financement (gameplay) ---
    loan_amount: float = 0.0
    monthly_loan_payment: float = 0.0
    charges_fixes: float = 0.0
    monthly_bpi: float = 0.0
    monthly_bank: float = 0.0

    # --- Coûts récurrents / marketing ---
    overheads: dict = field(default_factory=dict)
    marketing_budget: float = 0.0

    # --- Stock ---
    stock_value: float = 0.0

    # --- Module RH ---
    equipe: list = field(default_factory=list)
    type_resto: str = field(init=False)

    # --- Comptabilité / Emprunts ---
    bpi_outstanding: float = 0.0
    bank_outstanding: float = 0.0
    bpi_rate_annual: float = 0.025
    bank_rate_annual: float = 0.045
    ledger: object = None  # sera un Ledger

    def __post_init__(self):
        self.type_resto = self.type.name

    @property
    def capacity_per_turn(self) -> int:
        # mensuel: 2 services * 30 jours
        return self.local.capacite_clients * 2 * 30
