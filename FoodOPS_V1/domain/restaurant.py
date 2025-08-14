from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional, Tuple, Type

import numpy as np
from pydantic import BaseModel

from FoodOPS_V1.core.accounting import Ledger, TypeOperation, post_opening
from FoodOPS_V1.domain.ingredients import FoodGrade
from FoodOPS_V1.domain.inventory import Inventory
from FoodOPS_V1.domain.local import Local
from FoodOPS_V1.domain.recipe import SimpleRecipe
from FoodOPS_V1.domain.scenario import FinancingPlan
from FoodOPS_V1.domain.staff import Employe
from FoodOPS_V1.domain.types import RestaurantType

MARGIN_BY_RESTO = {"FAST_FOOD": 2.5, "BISTRO": 3.0, "GASTRO": 3.8}


class Restaurant(BaseModel):
    """Base restaurant with shared behavior/fields."""

    # Per-subclass constants
    TYPE: ClassVar[RestaurantType] = RestaurantType.FAST_FOOD
    DEFAULT_MARGIN: ClassVar[float] = 2.5
    SERVICE_SPEED: ClassVar[float] = 1.00
    SERVICE_MINUTES_PER_COVER: ClassVar[float] = 0.0
    preferences: List[FoodGrade] = field(default_factory=list)

    # Common fields
    name: str
    local: Local
    notoriety: float = 0.5  # entre 0.0 et 1.0
    equipe: List[Employe] = field(default_factory=list)
    marketing_budget: float = 0.0
    menu: List[SimpleRecipe] = field(default_factory=list)
    funds: float = 0.0
    ledger: Ledger = None
    equipment_invest: float = 0.0
    bpi_outstanding: float = 0.0
    bpi_rate_annual: float = 0.0
    monthly_bpi: float = 0.0
    bank_outstanding: float = 0.0
    bank_rate_annual: float = 0.0
    monthly_bank: float = 0.0
    charges_reccurentes: float = 0.0
    inventory: Inventory = field(default_factory=Inventory)
    turn_cogs: float = 0.0
    service_minutes_left: float = 0.0
    kitchen_minutes_left: float = 0.0
    rh_satisfaction: float = 0.0

    # Optional override per instance (kept if you need flexibility)
    margin_override: Optional[float] = None

    # Canonical margin always comes from subclass unless overridden
    @property
    def margin(self) -> float:
        return (
            self.margin_override
            if self.margin_override is not None
            else self.DEFAULT_MARGIN
        )

    # If you still want a "type" string for JSON/DB
    @property
    def type(self) -> str:
        return self.TYPE

    @property
    def service_speed(self) -> float:
        return self.SERVICE_SPEED

    def add_recipe_to_menu(self, recipe: SimpleRecipe) -> None:
        if all(r.name != recipe.name for r in self.menu):
            self.menu.append(recipe)

    def reset_rh_minutes(self) -> None:
        total_service = 0
        total_kitchen = 0
        for e in self.equipe or []:
            if hasattr(e, "compute_minutes"):
                e.compute_minutes()
            total_service += getattr(e, "service_minutes", 0)
            total_kitchen += getattr(e, "kitchen_minutes", 0)
        self.service_minutes_left = int(total_service)
        self.kitchen_minutes_left = int(total_kitchen)

    def consume_service_minutes(self, minutes: int) -> None:
        self.service_minutes_left = max(0, self.service_minutes_left - int(minutes))

    def consume_kitchen_minutes(self, minutes: int) -> None:
        self.kitchen_minutes_left = max(0, self.kitchen_minutes_left - int(minutes))

    def update_rh_satisfaction(self) -> None:
        total = getattr(self, "service_minutes_left", 0) + getattr(
            self, "kitchen_minutes_left", 0
        )
        used = 0
        for e in self.equipe or []:
            used += getattr(e, "service_minutes", 0) + getattr(e, "kitchen_minutes", 0)
        ratio = used / total if total else 0.0
        if ratio > 0.95:
            delta = -0.06
        elif ratio > 0.85:
            delta = -0.03
        elif ratio < 0.35:
            delta = -0.02
        elif ratio < 0.55:
            delta = +0.01
        else:
            delta = +0.02
        self.rh_satisfaction = max(
            0.0, min(1.0, getattr(self, "rh_satisfaction", 0.8) + delta)
        )

    def compute_exploitable_capacity(self) -> int:
        """
        Calcule la capacité exploitable mensuelle d'un restaurant.

        Cette fonction calcule combien de clients un restaurant peut théoriquement servir
        en un mois, en tenant compte de:
        - la capacité physique,
        - la fréquence de service,
        - la vitesse de service (selon le type de restaurant).

        Le calcul suppose :
        - 2 périodes de service par jour (déjeuner et dîner)
        - 30 jours par mois
        - La vitesse de service varie selon le type de restaurant (fast-food plus rapide que gastro)

        Args:
            restaurant: Objet Restaurant contenant la capacité du local et les informations de type

        Returns:
            Capacité exploitable mensuelle en tant qu'entier (nombre de clients)
            Retourne 0 si le calcul résulte en une valeur négative

        Example:
            Pour un bistro avec une capacité de 20 places :
            - Capacité mensuelle de base : 20 * 2 * 30 = 1200 clients
            - Coefficient de vitesse bistro : 0.80
            - Capacité exploitable : 1200 * 0.80 = 960 clients
        """
        # Nombre de périodes de service par jour
        nb_periods_per_day = 2
        # Nombre de jours par mois
        nb_days_per_month = 30
        base_monthly_capacity = (
            self.local.capacite_clients * nb_periods_per_day * nb_days_per_month
        )
        exploitable_capacity = base_monthly_capacity * self.service_speed
        return max(0, int(exploitable_capacity))

    # Enregistrement des écritures comptables

    def post_opening(self, financing_plan: FinancingPlan):
        lines = post_opening(
            cash=self.funds,  # tréso initiale
            equipment=self.equipment_invest,  # immobilisations
            loans_total=financing_plan.bank_loan
            + financing_plan.bpi_loan,  # dette initiale
        )
        self.ledger.post(0, "Ouverture", lines)

    def post_sales(self, tour: int, chiffre_affaires: float):
        if chiffre_affaires > 0:
            self.ledger.post(
                tour,
                "Ventes",
                [
                    ("512", chiffre_affaires, TypeOperation.DEBIT),
                    ("70", chiffre_affaires, TypeOperation.CREDIT),
                ],
            )
        else:
            print(f"Chiffre d'affaires négatif: {chiffre_affaires}")

    def post_cogs(self, tour: int, cogs: float):
        """Enregistre les achats consommés (CoGS) du tour."""
        if cogs > 0:
            self.ledger.post(
                tour,
                "Achats consommés (matières)",
                [
                    ("60", cogs, TypeOperation.DEBIT),
                    ("512", cogs, TypeOperation.CREDIT),
                ],
            )
        else:
            print(f"Coût des matières premières négatif: {cogs}")

    def post_services_ext(self, tour: int, amount: float):
        """Enregistre les services extérieurs (loyer, abonnements, marketing)."""
        if amount > 0:
            self.ledger.post(
                tour,
                "Services extérieurs (loyer, abonnements, marketing)",
                [
                    ("61", amount, TypeOperation.DEBIT),
                    ("512", amount, TypeOperation.CREDIT),
                ],
            )
        else:
            print(f"Montant des services extérieurs négatif: {amount}")

    def post_payroll(self, tour: int, payroll_total: float):
        """Enregistre les charges de personnel.

        Args:
            ledger: Grand livre à alimenter.
            tour: Tour courant (mois).
            payroll_total: Masse salariale totale (salaires + charges) payée.
        """
        if payroll_total > 0:
            lines = [
                ("64", payroll_total, TypeOperation.DEBIT),
                ("512", payroll_total, TypeOperation.CREDIT),
            ]
            self.ledger.post(tour, "Charges de personnel", lines)
        else:
            print(f"Montant des charges de personnel négatif: {payroll_total}")

    def post_depreciation(self, tour: int, dotation: float):
        """Enregistre la dotation aux amortissements du tour.

        Args:
            ledger: Grand livre à alimenter.
            tour: Tour courant (mois).
            dotation: Montant de la dotation de la période.
        """
        if dotation > 0:
            lines = [
                ("681", dotation, TypeOperation.DEBIT),
                ("2815", dotation, TypeOperation.CREDIT),
            ]
            self.ledger.post(tour, "Dotations aux amortissements", lines)
        else:
            print(f"Montant des dotations aux amortissements négatif: {dotation}")

    def post_loan_payment(
        self, tour: int, interest: float, principal: float, label: str
    ):
        """Enregistre un remboursement d'emprunt (intérêts et/ou capital).

        Args:
            ledger: Grand livre à alimenter.
            tour: Tour courant (mois).
            interest: Part d'intérêts payée (charge 66).
            principal: Part de capital remboursée (diminution du 164).
            label: Suffixe descriptif du prêt (ex: "banque A").
        """
        lines: List[Tuple[str, float, TypeOperation]] = []
        if interest < 0 or principal < 0:
            print(
                f"Montant d'intérêts ou de capital négatif: {interest} ou {principal}"
            )
        if interest > 0:
            lines.extend(
                ("66", interest, TypeOperation.DEBIT),
                ("512", interest, TypeOperation.CREDIT),
            )
        if principal > 0:
            lines.extend(
                ("164", principal, TypeOperation.DEBIT),
                ("512", principal, TypeOperation.CREDIT),
            )
        if lines:
            self.ledger.post(tour, f"Remboursement {label}", lines)

    def month_amortization(self) -> float:
        """Calcule la dotation d'amortissement mensuelle linéaire.

        La durée d'amortissement provient de `EQUIP_AMORT_YEARS`. Un tour
        correspond à un mois.

        Returns:
            Montant mensuel de la dotation (arrondi à 2 décimales). Retourne 0 si
            `amount <= 0`.
        """
        amount = self.equipment_invest
        EQUIP_AMORT_YEARS = 5  # Amortissement linéaire des équipements (années)
        months = EQUIP_AMORT_YEARS * 12  # Nombre de mois d'amortissement
        return 0.0 if amount <= 0 else round(amount / months, 2)

    # FIN - Enregistrement des écritures comptables

    def compute_median_price(self) -> float:
        """Prix médian des menus du restaurant."""
        prix_des_items = [item.price for item in self.menu if item is not None]
        return np.median(prix_des_items) if prix_des_items else 0.0

    def get_available_portions(self) -> int:
        """Retourne le nombre total de portions finies disponibles en stock.

        Returns:
            Nombre total de portions finies disponibles, ou 0 si aucune
        """
        return self.inventory.total_finished_portions()

    def _fixed_costs_of(self) -> float:
        """Calcule les coûts fixes mensuels totaux du restaurant.

        Args:
            restaurant: Restaurant dont calculer les coûts fixes

        Returns:
            Somme du loyer du local et des charges récurrentes mensuelles
        """
        # Somme du loyer du local et des charges récurrentes mensuelles
        return self.local.loyer + self.charges_reccurentes

    def _rh_cost_of(self) -> float:
        """Calcule le coût salarial mensuel total de l'équipe.

        Args:
            restaurant: Restaurant avec l'équipe à évaluer

        Returns:
            Somme de tous les salaires totaux de l'équipe, arrondie à 2 décimales
        """
        # Additionne tous les salaires de l'équipe et arrondit à 2 décimales
        return round(sum([employee.salaire_total for employee in self.equipe]), 2)

    def _service_minutes_per_cover(self) -> float:
        """Retourne le temps de service standard par couvert selon le type de restaurant.

        Args:
            rtype: Type de restaurant (FAST_FOOD, BISTRO, GASTRO)

        Returns:
            Durée en minutes pour servir un couvert de ce type de restaurant
        """
        # Récupère la durée de service depuis la constante globale selon le type de restaurant
        return float(self.SERVICE_MINUTES_PER_COVER)


@dataclass
class FastFoodRestaurant(Restaurant):
    TYPE: ClassVar[str] = "FAST_FOOD"
    DEFAULT_MARGIN: ClassVar[float] = 2.5
    SERVICE_SPEED: ClassVar[float] = 1.00
    preferences: List[FoodGrade] = [FoodGrade.G3_SURGELE, FoodGrade.G1_FRAIS_BRUT]
    SERVICE_MINUTES_PER_COVER: ClassVar[float] = 1.5


@dataclass
class BistroRestaurant(Restaurant):
    TYPE: ClassVar[str] = "BISTRO"
    DEFAULT_MARGIN: ClassVar[float] = 3.0
    SERVICE_SPEED: ClassVar[float] = 0.80
    preferences: List[FoodGrade] = [FoodGrade.G1_FRAIS_BRUT, FoodGrade.G3_SURGELE]
    SERVICE_MINUTES_PER_COVER: ClassVar[float] = 4.0


@dataclass
class GastroRestaurant(Restaurant):
    TYPE: ClassVar[str] = "GASTRO"
    DEFAULT_MARGIN: ClassVar[float] = 3.8
    SERVICE_SPEED: ClassVar[float] = 0.50
    preferences: List[FoodGrade] = [FoodGrade.G1_FRAIS_BRUT, FoodGrade.G3_SURGELE]
    SERVICE_MINUTES_PER_COVER: ClassVar[float] = 7.0


_REGISTRY: Dict[str, Type[Restaurant]] = {
    FastFoodRestaurant.TYPE: FastFoodRestaurant,
    BistroRestaurant.TYPE: BistroRestaurant,
    GastroRestaurant.TYPE: GastroRestaurant,
}


def make_restaurant(kind: str, **kwargs) -> Restaurant:
    """Factory that replaces enum->class mapping for deserialization/creation."""
    cls = _REGISTRY.get(kind)
    if not cls:
        raise ValueError(f"Unknown restaurant kind: {kind}")
    return cls(**kwargs)
