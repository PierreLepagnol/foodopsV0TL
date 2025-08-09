# -*- coding: utf-8 -*-
# foodops/domain/inventory.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# On importe la notion de gamme pour pouvoir prioriser “meilleure gamme d’abord”.
try:
    from .ingredients import FoodGrade
except Exception:
    # Fallback minimal si le module n’est pas encore en place.
    class FoodGrade:  # type: ignore
        G1_FRAIS_BRUT = 1
        G2_CONSERVE = 2
        G3_SURGELE = 3
        G4_CRU_PRET = 4
        G5_CUIT_SOUS_VIDE = 5

# Classement “qualité perçue” des gammes (plus haut = meilleur).
# Ajustable si besoin.
_GRADE_RANK: Dict[FoodGrade, int] = {
    getattr(FoodGrade, "G5_CUIT_SOUS_VIDE"): 5,
    getattr(FoodGrade, "G4_CRU_PRET"): 4,
    getattr(FoodGrade, "G1_FRAIS_BRUT"): 3,
    getattr(FoodGrade, "G3_SURGELE"): 2,
    getattr(FoodGrade, "G2_CONSERVE"): 1,
}

def _grade_rank(g: FoodGrade) -> int:
    return _GRADE_RANK.get(g, 0)


# -------------------- Lots d’inventaire --------------------

@dataclass
class IngredientStockLot:
    """
    Lot d’ingrédient en stock.
    - perish_tour : dernier tour où le lot est consommable (exclu après cleanup).
    """
    name: str
    grade: FoodGrade
    qty_kg: float
    unit_cost: float
    received_tour: int
    perish_tour: int

    def is_expired(self, current_tour: int) -> bool:
        return current_tour > self.perish_tour


@dataclass
class FinishedBatch:
    """
    Lot de produits finis prêts à vendre.
    - expires_tour : dernier tour où la vente est possible (périme au tour suivant la prod par défaut).
    """
    recipe_name: str
    selling_price: float
    portions: int
    produced_tour: int
    expires_tour: int

    def is_expired(self, current_tour: int) -> bool:
        return current_tour > self.expires_tour


# -------------------- Inventory principal --------------------

@dataclass
class Inventory:
    """
    Stock du restaurant :
      - raw[name] -> liste de lots d’ingrédients (multi-gammes)
      - finished  -> liste de lots de produits finis (FIFO de vente)
    """
    raw: Dict[str, List[IngredientStockLot]] = field(default_factory=dict)
    finished: List[FinishedBatch] = field(default_factory=list)

    # -------- Ingrédients (achats / disponibilité / consommation) --------

    def add_ingredient(
        self,
        name: str,
        grade: FoodGrade,
        qty_kg: float,
        unit_cost: float,
        current_tour: int,
        shelf_tours: int = 1,
    ) -> None:
        """
        Ajoute un lot d’ingrédient. La péremption est exprimée en nombre de tours.
        Par ex. shelf_tours=1 => consommable sur le tour courant seulement.
        """
        lot = IngredientStockLot(
            name=name,
            grade=grade,
            qty_kg=float(qty_kg),
            unit_cost=float(unit_cost),
            received_tour=current_tour,
            perish_tour=current_tour + int(max(0, shelf_tours)),
        )
        self.raw.setdefault(name, []).append(lot)

    def get_available_qty(self, name: str, current_tour: Optional[int] = None) -> float:
        """
        Quantité totale dispo (kg) non périmée pour un ingrédient.
        """
        lots = self.raw.get(name, [])
        total = 0.0
        for lot in lots:
            if current_tour is not None and lot.is_expired(current_tour):
                continue
            total += max(0.0, lot.qty_kg)
        return round(total, 6)

    def has_ingredient(self, name: str, qty_needed_kg: float, current_tour: Optional[int] = None) -> bool:
        """
        True si la somme des lots non périmés couvre qty_needed_kg.
        """
        return self.get_available_qty(name, current_tour) >= float(qty_needed_kg)

    def _iter_lots_best_quality_fifo(self, name: str, current_tour: Optional[int]) -> List[IngredientStockLot]:
        """
        Retourne les lots ordonnés par :
          1) meilleure gamme d’abord (rank décroissant)
          2) ancienneté (FIFO dans une même gamme)
        Les lots périmés sont exclus.
        """
        lots = [lot for lot in self.raw.get(name, []) if not (current_tour and lot.is_expired(current_tour))]
        # Tri : meilleure gamme d’abord (-rank), puis received_tour croissant (ancien d’abord)
        lots.sort(key=lambda l: (-_grade_rank(l.grade), l.received_tour))
        return lots

    def consume_ingredient(
        self,
        name: str,
        qty_needed_kg: float,
        current_tour: Optional[int] = None,
    ) -> Tuple[float, float]:
        """
        Consomme jusqu’à qty_needed_kg en priorisant la meilleure gamme puis FIFO.
        Retourne (qty_retirée, coût_total_consumé). Si la quantité dispo est insuffisante,
        consommera le maximum possible (et retournera une quantité < qty_needed_kg).

        NOTE : on ne mixe pas de logique de coût “cible” ici ; on valorise au coût unitaire du lot.
        """
        need = float(qty_needed_kg)
        taken = 0.0
        cost = 0.0

        if need <= 0:
            return (0.0, 0.0)

        lots = self._iter_lots_best_quality_fifo(name, current_tour)
        i = 0
        while i < len(lots) and need > 0:
            lot = lots[i]
            take = min(lot.qty_kg, need)
            if take > 0:
                lot.qty_kg -= take
                taken += take
                cost += take * lot.unit_cost
                need -= take

            if lot.qty_kg <= 1e-9:
                # supprimer le lot vide du “vrai” tableau
                real_lots = self.raw.get(name, [])
                try:
                    idx_real = real_lots.index(lot)
                    real_lots.pop(idx_real)
                except ValueError:
                    pass
                lots.pop(i)
            else:
                i += 1

        return (round(taken, 6), round(cost, 2))

    # -------- Produits finis (production / vente / nettoyage) --------

    def add_finished_lot(
        self,
        recipe_name: str,
        selling_price: float,
        portions: int,
        produced_tour: int,
        shelf_tours: int = 1,
    ) -> None:
        """
        Ajoute un lot de produits finis. Par défaut, périme au tour suivant (shelf_tours=1).
        """
        batch = FinishedBatch(
            recipe_name=recipe_name,
            selling_price=float(selling_price),
            portions=int(portions),
            produced_tour=produced_tour,
            expires_tour=produced_tour + int(max(0, shelf_tours)),
        )
        self.finished.append(batch)

    def total_finished_portions(self, recipe_name: Optional[str] = None, current_tour: Optional[int] = None) -> int:
        """
        Nombre total de portions prêtes à vendre (non périmées). Si recipe_name est fourni, filtre.
        """
        total = 0
        for b in self.finished:
            if current_tour is not None and b.is_expired(current_tour):
                continue
            if recipe_name is not None and b.recipe_name != recipe_name:
                continue
            total += max(0, int(b.portions))
        return total

    def sell_from_finished_fifo(self, qty_portions: int) -> Tuple[int, float]:
        """
        Vend jusqu’à qty_portions (peu importe la recette), FIFO strict.
        Retourne (portions_vendues, chiffre_affaires).
        NB : certaines UIs préféreront choisir une recette précise — cette
        méthode globale est utile quand on “sert” des clients sans granularité.
        """
        need = int(qty_portions)
        sold = 0
        revenue = 0.0
        i = 0
        while i < len(self.finished) and need > 0:
            b = self.finished[i]
            if b.portions <= 0:
                self.finished.pop(i)
                continue
            take = min(b.portions, need)
            if take > 0:
                sold += take
                revenue += take * b.selling_price
                b.portions -= take
                need -= take

            if b.portions <= 0:
                self.finished.pop(i)
            else:
                i += 1
        return (sold, round(revenue, 2))

    # -------- Nettoyage (péremption) --------

    def cleanup_expired(self, current_tour: int) -> None:
        """
        Supprime tous les lots périmés (ingrédients & produits finis).
        À appeler au début de chaque tour.
        """
        # Ingrédients
        for name, lots in list(self.raw.items()):
            keep: List[IngredientStockLot] = []
            for lot in lots:
                if lot.is_expired(current_tour):
                    continue
                # on garde uniquement les quantités positives
                if lot.qty_kg > 1e-9:
                    keep.append(lot)
            if keep:
                self.raw[name] = keep
            else:
                self.raw.pop(name, None)

        # Produits finis
        self.finished = [b for b in self.finished if not b.is_expired(current_tour)]

    # -------- Aides diverses --------

    def available_grades(self, name: str, current_tour: Optional[int] = None) -> List[FoodGrade]:
        """
        Liste des gammes disponibles (non périmées) pour un ingrédient donné,
        triées de la meilleure à la moins bonne.
        """
        lots = self._iter_lots_best_quality_fifo(name, current_tour)
        grades = []
        seen = set()
        for l in lots:
            if l.grade not in seen:
                seen.add(l.grade)
                grades.append(l.grade)
        return grades

    def snapshot(self, current_tour: Optional[int] = None) -> Dict[str, List[Tuple[str, float]]]:
        """
        Vue simple du stock : {ingredient: [(grade, qty_kg), ...]} (non périmé uniquement si current_tour fourni)
        """
        snap: Dict[str, List[Tuple[str, float]]] = {}
        for name, lots in self.raw.items():
            rows: List[Tuple[str, float]] = []
            for l in lots:
                if current_tour is not None and l.is_expired(current_tour):
                    continue
                rows.append((getattr(l.grade, "name", str(l.grade)), round(l.qty_kg, 3)))
            # tri visuel : meilleure gamme d’abord
            rows.sort(key=lambda gq: -_grade_rank(getattr(FoodGrade, gq[0], gq[0]) if isinstance(gq[0], str) else gq[0]))
            if rows:
                snap[name] = rows
        return snap
