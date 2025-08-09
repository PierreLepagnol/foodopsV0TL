from dataclasses import dataclass

@dataclass(frozen=True)
class Recipe:
    name: str
    selling_price: float  # € par couvert
    base_quality: float   # 0..1 (sera remplacé par qualité ingrédients/gammes)
    # TODO: Ajouter des attributs pour les ingrédients et les gammes
    