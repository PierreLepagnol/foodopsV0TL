from .inventory import Inventory
from ..domain.rh import StaffMember, Role, ALLOWED_ROLES, ROLE_PRODUCTIVITY, ROLE_BANK
from dataclasses import dataclass, field
from enum import Enum
from typing import List, TYPE_CHECKING
from .local import Local
from .stock import Inventory
from ..rules.labour import recipe_prep_minutes_per_portion

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

    # --- Inventaire & COGS ---
    inventory: Inventory = field(default_factory=Inventory)
    turn_cogs: float = 0.0  # COGS reconnus à la production sur le tour

    # --- Module RH ---
    equipe: list = field(default_factory=list)

    # banques RH par tour
    prod_minutes_total: int = 0
    prod_minutes_left: int = 0
    service_minutes_total: int = 0
    service_minutes_left: int = 0
    rh_satisfaction: float = 0.80

    def reset_rh_minutes(self):
        prod = 0
        serv = 0
        for m in self.equipe:
            if m.role not in ALLOWED_ROLES.get(self.type, set()):
                continue
            minutes = int(m.heures_par_tour * ROLE_PRODUCTIVITY.get(m.role, 0))
            bank = ROLE_BANK.get(m.role)
            if bank == "prod":
                prod += minutes
            elif bank == "service":
                serv += minutes
        self.prod_minutes_total = self.prod_minutes_left = prod
        self.service_minutes_total = self.service_minutes_left = serv

    def consume_prod_minutes(self, minutes: int) -> bool:
        if minutes <= self.prod_minutes_left:
            self.prod_minutes_left -= minutes
            return True
        return False

    def consume_service_minutes(self, minutes: int) -> bool:
        if minutes <= self.service_minutes_left:
            self.service_minutes_left -= minutes
            return True
        return False

    def update_rh_satisfaction(self):
        # Utilisation combinée (prod + service)
        tot = self.prod_minutes_total + self.service_minutes_total
        used = (self.prod_minutes_total - self.prod_minutes_left) + (self.service_minutes_total - self.service_minutes_left)
        util = (used / tot) if tot else 0.0
        if util > 0.95:   delta = -0.06
        elif util > 0.85: delta = -0.03
        elif util < 0.35: delta = -0.02
        elif util < 0.55: delta = +0.01
        else:             delta = +0.02
        self.rh_satisfaction = max(0.0, min(1.0, self.rh_satisfaction + delta))
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

    def prepare_recipe(self, recipe, portions):
        mins_pp = recipe_prep_minutes_per_portion(recipe)
        mins_need = int(round(mins_pp * portions))
        if not self.consume_prod_minutes(mins_need):
            # calcul du max possible
            max_portions = self.prod_minutes_left // max(1, int(mins_pp))
            if max_portions <= 0:
                print("❌ Équipe cuisine saturée ce tour.")
                return
            print(f"⚠️ Capacité cuisine limite: plafonné à {max_portions} portions.")
            portions = max_portions
            self.consume_prod_minutes(int(round(mins_pp * portions)))
