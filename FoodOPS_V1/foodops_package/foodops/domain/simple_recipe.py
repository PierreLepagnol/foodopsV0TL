from dataclasses import dataclass
from enum import Enum
from typing import Optional

# === Ajout pour compatibilité menus_presets_simple ===
class Technique(str, Enum):
    FROID = "froid"
    GRILLE = "grillé"
    SAUTE = "sauté"

class Complexity(str, Enum):
    SIMPLE = "simple"
    COMPLEXE = "complexe"

@dataclass
class SimpleRecipe:
    name: str
    base_quality: float
    base_cost: float
    selling_price: float
    technique: Optional[Technique] = None
    complexity: Optional[Complexity] = None

    def __post_init__(self):
        if self.base_quality < 0:
            self.base_quality = 0
        elif self.base_quality > 1:
            self.base_quality = 1
        if self.base_cost < 0:
            self.base_cost = 0
        if self.selling_price < 0:
            self.selling_price = 0

    def profit_margin(self) -> float:
        if self.selling_price <= 0:
            return 0.0
        return (self.selling_price - self.base_cost) / self.selling_price

    def clone_with_price(self, new_price: float):
        return SimpleRecipe(
            name=self.name,
            base_quality=self.base_quality,
            base_cost=self.base_cost,
            selling_price=new_price,
            technique=self.technique,
            complexity=self.complexity
        )
