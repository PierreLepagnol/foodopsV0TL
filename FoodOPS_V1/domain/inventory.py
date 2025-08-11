from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from FoodOPS_V1.domain.ingredients import FoodGrade


# Classement “qualité perçue” des gammes (plus haut = meilleur).
# Ajustable si besoin.
_GRADE_RANK: Dict[FoodGrade, int] = {
    FoodGrade.G5_CUIT_SOUS_VIDE: 5,
    FoodGrade.G1_FRAIS_BRUT: 3,
    FoodGrade.G3_SURGELE: 2,
    FoodGrade.G2_CONSERVE: 1,
}


# -------------------- Lots d'inventaire --------------------


@dataclass
class IngredientStockLot:
    """
    Lot d'ingrédient en stock.
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
      - raw[name] -> liste de lots d'ingrédients (multi-gammes)
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
        Ajoute un lot d'ingrédient. La péremption est exprimée en nombre de tours.
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

    def has_ingredient(
        self,
        name: str,
        qty_needed_kg: float,
        current_tour: Optional[int] = None,
    ) -> bool:
        """
        True si la somme des lots non périmés couvre qty_needed_kg.
        """
        return self.get_available_qty(name, current_tour) >= float(qty_needed_kg)

    def _iter_lots_best_quality_fifo(
        self, name: str, current_tour: Optional[int]
    ) -> List[IngredientStockLot]:
        """
        Retourne les lots ordonnés par :
          1) meilleure gamme d'abord (rank décroissant)
          2) ancienneté (FIFO dans une même gamme)
        Les lots périmés sont exclus.
        """
        lots = [
            lot
            for lot in self.raw.get(name, [])
            if not (current_tour and lot.is_expired(current_tour))
        ]
        # Tri : meilleure gamme d'abord (-rank), puis received_tour croissant (ancien d'abord)
        lots.sort(key=lambda l: (-_GRADE_RANK[l.grade], l.received_tour))
        return lots

    def consume_ingredient(
        self,
        name: str,
        qty_needed_kg: float,
        current_tour: Optional[int] = None,
    ) -> Tuple[float, float]:
        """
        Consomme jusqu'à qty_needed_kg en priorisant la meilleure gamme puis FIFO.
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

    def total_finished_portions(
        self,
        recipe_name: Optional[str] = None,
        current_tour: Optional[int] = None,
    ) -> int:
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
        Vend jusqu'à qty_portions (peu importe la recette), FIFO strict.
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

    def available_grades(
        self, name: str, current_tour: Optional[int] = None
    ) -> List[FoodGrade]:
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

    def snapshot(
        self, current_tour: Optional[int] = None
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Vue simple du stock : {ingredient: [(grade, qty_kg), ...]} (non périmé uniquement si current_tour fourni)

        Étapes du processus:
        1. Parcourt tous les ingrédients dans self.raw
        2. Pour chaque ingrédient, examine tous ses lots
        3. Filtre les lots périmés si current_tour est fourni
        4. Extrait le nom de la gamme et la quantité de chaque lot valide
        5. Trie les résultats par qualité de gamme (meilleure d'abord)
        6. Retourne un dictionnaire organisé

        Exemple:
        Si self.raw = {
            "tomate": [
                IngredientStockLot(name="tomate", grade=FoodGrade.G1_FRAIS_BRUT, qty_kg=2.5, ...),
                IngredientStockLot(name="tomate", grade=FoodGrade.G2_CONSERVE, qty_kg=1.0, ...)
            ],
            "oignon": [
                IngredientStockLot(name="oignon", grade=FoodGrade.G3_SURGELE, qty_kg=0.8, ...)
            ]
        }

        Retourne:
        {
            "tomate": [("G1_FRAIS_BRUT", 2.5), ("G2_CONSERVE", 1.0)],  # trié par qualité
            "oignon": [("G3_SURGELE", 0.8)]
        }
        """
        snap: Dict[str, List[Tuple[str, float]]] = {}

        # Étape 1: Parcourir tous les ingrédients
        for name, lots in self.raw.items():
            rows: List[Tuple[str, float]] = []

            # Étape 2: Examiner chaque lot de l'ingrédient
            for l in lots:
                # Étape 3: Filtrer les lots périmés si nécessaire
                if current_tour is not None and l.is_expired(current_tour):
                    continue

                # Étape 4: Extraire nom de gamme et quantité
                grade_name = getattr(l.grade, "name", str(l.grade))
                quantity = round(l.qty_kg, 3)
                rows.append((grade_name, quantity))

            # Étape 5: Trier par qualité de gamme (meilleure d'abord)
            rows.sort(
                key=lambda gq: -_GRADE_RANK.get(
                    getattr(FoodGrade, gq[0], gq[0])
                    if isinstance(gq[0], str)
                    else gq[0],
                    0,  # valeur par défaut si gamme inconnue
                )
            )

            # Étape 6: Ajouter au résultat final si des lots valides existent
            if rows:
                snap[name] = rows

        return snap


# LEGACY


# from dataclasses import dataclass, field
# from typing import Dict, List, Tuple
# from FoodOPS_V1.data.ingredients import Ingredient, FoodGrade
# from FoodOPS_V1.domain.simple_recipe import SimpleRecipe
# from FoodOPS_V1.rules.costing import compute_recipe_cogs


# @dataclass
# class StockItem:
#     ingredient: Ingredient
#     kg: float  # quantité en kg disponible


# @dataclass
# class FinishedBatch:
#     recipe_name: str
#     selling_price: float
#     portions: int
#     expiry_tour: int  # périme après ce tour


# @dataclass
# class Inventory:
#     ingredients: Dict[Tuple[str, FoodGrade], StockItem] = field(default_factory=dict)
#     finished: List[FinishedBatch] = field(default_factory=list)

#     # --- INGREDIENTS ---

#     def add_ingredient(self, ing: Ingredient, kg: float) -> None:
#         key = (ing.name, ing.grade)
#         cur = self.ingredients.get(key)
#         if cur:
#             cur.kg += kg
#         else:
#             self.ingredients[key] = StockItem(ingredient=ing, kg=kg)

#     def get_available_variants(self, name: str) -> List[StockItem]:
#         return [
#             si
#             for (n, _), si in self.ingredients.items()
#             if n == name and si.kg > 0.0001
#         ]

#     def consume_ingredient(self, ing: Ingredient, kg: float) -> bool:
#         key = (ing.name, ing.grade)
#         si = self.ingredients.get(key)
#         if not si or si.kg < kg - 1e-9:
#             return False
#         si.kg -= kg
#         if si.kg <= 1e-6:
#             del self.ingredients[key]
#         return True

#     # --- PRODUITS FINIS ---

#     def cleanup_expired(self, current_tour: int) -> None:
#         self.finished = [b for b in self.finished if b.expiry_tour >= current_tour]

#     def total_finished_portions(self) -> int:
#         return sum(b.portions for b in self.finished)

#     def consume_finished(self, qty: int) -> int:
#         """Consomme des portions FIFO. Retourne réellement consommé."""
#         need = qty
#         i = 0
#         while i < len(self.finished) and need > 0:
#             b = self.finished[i]
#             take = min(b.portions, need)
#             b.portions -= take
#             need -= take
#             if b.portions == 0:
#                 self.finished.pop(i)
#             else:
#                 i += 1
#         return qty - need  # vendu

#     # --- PRODUCTION ---

#     def produce_from_recipe(
#         self, recipe: SimpleRecipe, portions: int, current_tour: int
#     ) -> Tuple[bool, float, str]:
#         """
#         Tente de produire 'portions' en consommant l'ingrédient principal du stock.
#         Retour: (ok, cogs_total, message).
#         Le coût reconnu est le COGS par portion * portions (reconnu à la production).
#         """
#         if portions <= 0:
#             return (False, 0.0, "Nombre de portions invalide.")

#         # Calcul quantité matière nécessaire
#         kg_needed = recipe.portion_kg * portions

#         # On doit utiliser exactement la variante (gamme) de l'ingrédient de la recette
#         key = (recipe.main_ingredient.name, recipe.main_ingredient.grade)
#         si = self.ingredients.get(key)
#         if not si or si.kg < kg_needed - 1e-9:
#             return (
#                 False,
#                 0.0,
#                 "Stock insuffisant pour cette gamme d'ingrédient.",
#             )

#         # Déduire du stock
#         si.kg -= kg_needed
#         if si.kg <= 1e-6:
#             del self.ingredients[key]

#         # Créer un lot de produits finis périmant fin du tour suivant
#         batch = FinishedBatch(
#             recipe_name=recipe.name,
#             selling_price=recipe.selling_price,
#             portions=portions,
#             expiry_tour=current_tour + 1,
#         )
#         self.finished.append(batch)

#         # Coût reconnu à la production (matières + petit forfait MO/énergie)
#         cogs_one = compute_recipe_cogs(recipe)
#         cogs_total = round(cogs_one * portions, 2)
#         return (
#             True,
#             cogs_total,
#             f"Produit {portions} portions de « {recipe.name} » (péremption T{current_tour + 1}).",
#         )
