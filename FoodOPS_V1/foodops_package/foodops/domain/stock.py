# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from ..data.ingredients import Ingredient, FoodGrade
from ..domain.simple_recipe import SimpleRecipe
from ..rules.costing import compute_recipe_cogs

@dataclass
class StockItem:
    ingredient: Ingredient
    kg: float  # quantité en kg disponible

@dataclass
class FinishedBatch:
    recipe_name: str
    selling_price: float
    portions: int
    expiry_tour: int  # périme après ce tour

@dataclass
class Inventory:
    ingredients: Dict[Tuple[str, FoodGrade], StockItem] = field(default_factory=dict)
    finished: List[FinishedBatch] = field(default_factory=list)

    # --- INGREDIENTS ---

    def add_ingredient(self, ing: Ingredient, kg: float) -> None:
        key = (ing.name, ing.grade)
        cur = self.ingredients.get(key)
        if cur:
            cur.kg += kg
        else:
            self.ingredients[key] = StockItem(ingredient=ing, kg=kg)

    def get_available_variants(self, name: str) -> List[StockItem]:
        return [si for (n, _), si in self.ingredients.items() if n == name and si.kg > 0.0001]

    def consume_ingredient(self, ing: Ingredient, kg: float) -> bool:
        key = (ing.name, ing.grade)
        si = self.ingredients.get(key)
        if not si or si.kg < kg - 1e-9:
            return False
        si.kg -= kg
        if si.kg <= 1e-6:
            del self.ingredients[key]
        return True

    # --- PRODUITS FINIS ---

    def cleanup_expired(self, current_tour: int) -> None:
        self.finished = [b for b in self.finished if b.expiry_tour >= current_tour]

    def total_finished_portions(self) -> int:
        return sum(b.portions for b in self.finished)

    def consume_finished(self, qty: int) -> int:
        """Consomme des portions FIFO. Retourne réellement consommé."""
        need = qty
        i = 0
        while i < len(self.finished) and need > 0:
            b = self.finished[i]
            take = min(b.portions, need)
            b.portions -= take
            need -= take
            if b.portions == 0:
                self.finished.pop(i)
            else:
                i += 1
        return qty - need  # vendu

    # --- PRODUCTION ---

    def produce_from_recipe(self, recipe: SimpleRecipe, portions: int, current_tour: int) -> Tuple[bool, float, str]:
        """
        Tente de produire 'portions' en consommant l'ingrédient principal du stock.
        Retour: (ok, cogs_total, message).
        Le coût reconnu est le COGS par portion * portions (reconnu à la production).
        """
        if portions <= 0:
            return (False, 0.0, "Nombre de portions invalide.")

        # Calcul quantité matière nécessaire
        kg_needed = recipe.portion_kg * portions

        # On doit utiliser exactement la variante (gamme) de l'ingrédient de la recette
        key = (recipe.main_ingredient.name, recipe.main_ingredient.grade)
        si = self.ingredients.get(key)
        if not si or si.kg < kg_needed - 1e-9:
            return (False, 0.0, "Stock insuffisant pour cette gamme d'ingrédient.")

        # Déduire du stock
        si.kg -= kg_needed
        if si.kg <= 1e-6:
            del self.ingredients[key]

        # Créer un lot de produits finis périmant fin du tour suivant
        batch = FinishedBatch(
            recipe_name=recipe.name,
            selling_price=recipe.selling_price,
            portions=portions,
            expiry_tour=current_tour + 1
        )
        self.finished.append(batch)

        # Coût reconnu à la production (matières + petit forfait MO/énergie)
        cogs_one = compute_recipe_cogs(recipe)
        cogs_total = round(cogs_one * portions, 2)
        return (True, cogs_total, f"Produit {portions} portions de « {recipe.name} » (péremption T{current_tour+1}).")
