from dataclasses import dataclass

@dataclass(frozen=True)
class Local:
    nom: str
    surface: float
    visibilite: int
    loyer: float
    prix_fond: float
    capacite_clients: int
    equipement_facteur: float = 1.0
