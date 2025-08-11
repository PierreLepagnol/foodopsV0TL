from FoodOPS_V1.domain.local import Local

# Ajout d'un champ equipement_facteur dans Local (⚠️ Assure-toi que la dataclass Local a bien ce champ)
# Si ce n'est pas déjà fait : ouvre foodops/domain/local.py et ajoute: equipement_facteur: float

LOCALS = [
    Local(
        name="Petit local centre-ville",
        surface=50.0,
        visibility=5,
        loyer_mensuel=3000.0,
        prix_fond=100000.0,
        capacite_clients=40,
        equipement_facteur=0.90,
    ),
    Local(
        name="Local moyen centre-ville",
        surface=120.0,
        visibility=4,
        loyer_mensuel=7000.0,
        prix_fond=200000.0,
        capacite_clients=100,
        equipement_facteur=1.10,
    ),
    Local(
        name="Grand local banlieue",
        surface=200.0,
        visibility=3,
        loyer_mensuel=6000.0,
        prix_fond=150000.0,
        capacite_clients=120,
        equipement_facteur=1.20,
    ),
]
