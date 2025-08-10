from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import Field

from FoodOPS_V1.domain.types import RestaurantType
from FoodOPS_V1.domain.inventory import Inventory
from FoodOPS_V1.domain.recipe import SimpleRecipe
from FoodOPS_V1.domain.staff import Employe
from FoodOPS_V1.domain.local import Local


@dataclass
class Restaurant:
    name: str
    type: RestaurantType
    local: Local
    notoriety: float = Field(default=0.5, strict=True, ge=0, le=1)
    equipe: List["Employe"] = field(default_factory=list)
    marketing_budget: float = 0.0
    menu: List[SimpleRecipe] = field(default_factory=list)
    funds: float = 0.0
    ledger: Optional[object] = None
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
    service_minutes_left: int = 0
    kitchen_minutes_left: int = 0
    rh_satisfaction: float = 0.0

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
        # zone de confort 55-85% d'utilisation
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

    def _resolve_recipe_needs(self, recipe: SimpleRecipe) -> list:
        """Retourne la liste des besoins ingrédients [(name, qty_kg)] pour une recette."""
        needs = []
        if hasattr(recipe, "main_ingredient") and hasattr(recipe, "portion_kg"):
            needs.append((recipe.main_ingredient, recipe.portion_kg))
        elif hasattr(recipe, "ingredients"):
            # Poids par défaut : prot 0.15 kg, accompagnement 0.10 kg
            for ing in recipe.ingredients:
                name = ing[0] if isinstance(ing, tuple) else ing
                # grade = ing[1] if isinstance(ing, tuple) and len(ing) > 1 else None
                qty = 0.15 if "prot" in name.lower() else 0.10
                needs.append((name, qty))
        return needs
