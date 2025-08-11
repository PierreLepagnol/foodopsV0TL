from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


# === Ajout pour compatibilité menus_presets_simple ===
class Technique(Enum):
    FROID = auto()
    GRILLE = auto()
    SAUTE = auto()
    FOUR = auto()  # cuisson au four / rôtir
    ROTI = FOUR  # ✅ alias rétro-compat: Technique.ROTI existe
    FRIT = auto()
    VAPEUR = auto()


class Complexity(str, Enum):
    SIMPLE = "simple"
    COMPLEXE = "complexe"
    COMBO = "combo"


@dataclass
class SimpleRecipe:
    name: str
    # Deux formats acceptés
    ingredients: Optional[list] = None
    main_ingredient: Optional[object] = None
    portion_kg: float = 0.0

    technique: Optional[Technique] = None
    complexity: Optional[Complexity] = None

    base_quality: float = 0.8
    base_cost: float = 0.0

    price: float = 0.0  # utilisé par le moteur / scoring
    selling_price: float = 0.0  # alias pour compat

    def __post_init__(self):
        if self.base_quality < 0:
            self.base_quality = 0
        elif self.base_quality > 1:
            self.base_quality = 1
        if self.base_cost < 0:
            self.base_cost = 0
        if self.selling_price < 0:
            self.selling_price = 0
        if self.price < 0:
            self.price = 0

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
            price=new_price,
            technique=self.technique,
            complexity=self.complexity,
        )

    @property
    def effective_price(self) -> float:
        return float(self.price or self.selling_price or 0.0)

    def set_price(self, value):
        v = float(value)
        self.price = v
        self.selling_price = v


# LEGACY

# from dataclasses import dataclass


# @dataclass(frozen=True)
# class Recipe:
#     name: str
#     selling_price: float  # € par couvert
#     base_quality: float  # 0..1 (sera remplacé par qualité ingrédients/gammes)
#     # TODO: Ajouter des attributs pour les ingrédients et les gammes
