from dataclasses import dataclass, field
from typing import List, Dict
from .ingredient import Ingredient
from ..rules import costing


@dataclass(frozen=True)
class PrepStep:
    """Étape de prépa impactant la masse utile (parage, cuisson, évaporation, etc.)."""
    name: str
    loss_ratio: float  # ex: 0.1 = -10%


@dataclass
class RecipeLine:
    ingredient: Ingredient
    qty_g: float
    prep: List[PrepStep] = field(default_factory=list)

    def net_qty_g(self) -> float:
        """Quantité nette après pertes techniques (enchaînement des losses)."""
        net = self.qty_g
        for step in self.prep:
            net = costing.apply_loss(net, step.loss_ratio)
        return max(0.0, net)

    def line_cost(self, price_overrides: Dict[str, float] | None = None) -> float:
        """Coût d’achat pour la quantité brute (avant pertes) avec prix €/kg (overrides possible)."""
        p = (price_overrides or {}).get(self.ingredient.name, self.ingredient.base_price_eur_per_kg)
        return (self.qty_g / 1000.0) * p


@dataclass
class Recipe:
    name: str
    lines: List[RecipeLine]
    yield_portions: int
    selling_price: float = 0.0  # le joueur peut forcer; sinon on proposera via policy
    base_quality: float = 0.0   # on calcule une qualité de base (0..1) à partir des grades

    # --------- COÛTS ---------
    def raw_cost(self, price_overrides: Dict[str, float] | None = None) -> float:
        """Coût total matières (quantités brutes)."""
        return sum(line.line_cost(price_overrides) for line in self.lines)

    def cost_per_portion(self, price_overrides: Dict[str, float] | None = None) -> float:
        """Coût matières / portion en tenant compte du rendement."""
        if self.yield_portions <= 0:
            return 0.0
        total_cost = self.raw_cost(price_overrides)
        # V1 simple : on répartit le coût matières sur le nombre de portions annoncé
        return total_cost / self.yield_portions

    # --------- QUALITÉ ---------
    def estimate_quality(self) -> float:
        """Qualité perçue (0..1) selon les grades + pénalités/pertes (V1 : moyenne pondérée simple)."""
        if not self.lines:
            return 0.0
        weights = []
        vals = []
        for line in self.lines:
            g_weight = costing.GRADE_QUALITY_WEIGHTS.get(line.ingredient.grade, 0.6)
            vals.append(g_weight)
            weights.append(max(1.0, line.qty_g))  # pondération par masse
        q = sum(v * w for v, w in zip(vals, weights)) / sum(weights)
        self.base_quality = q
        return q

    # --------- PRIX CONSEILLÉ ---------
    def suggest_price(self, policy: costing.PricePolicy) -> float:
        """Prix conseillé FR en fonction d’une politique type (fast/bistro/gastro)."""
        cm = self.cost_per_portion()
        return costing.suggest_price(cm, policy)
