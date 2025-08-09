# -*- coding: utf-8 -*-
"""
Profils de postes pour les différents types de restaurants.
Chaque poste a un salaire marché brut mensuel, une capacité en couverts/tour,
et un impact sur la qualité du service.
"""

ROLES = {
    "FAST_FOOD": [
        {"nom": "Manager", "salaire_marche": 2200, "capacite_couverts": 120, "impact_qualite": 0.6, "categorie": "direction"},
        {"nom": "Équipier polyvalent", "salaire_marche": 1600, "capacite_couverts": 80, "impact_qualite": 0.5, "categorie": "salle"},
        {"nom": "Plongeur", "salaire_marche": 1500, "capacite_couverts": 40, "impact_qualite": 0.2, "categorie": "cuisine"},
    ],
    "BISTRO": [
        {"nom": "Chef", "salaire_marche": 2500, "capacite_couverts": 60, "impact_qualite": 0.8, "categorie": "cuisine"},
        {"nom": "Second de cuisine", "salaire_marche": 2000, "capacite_couverts": 50, "impact_qualite": 0.7, "categorie": "cuisine"},
        {"nom": "Serveur", "salaire_marche": 1600, "capacite_couverts": 40, "impact_qualite": 0.5, "categorie": "salle"},
        {"nom": "Plongeur", "salaire_marche": 1500, "capacite_couverts": 30, "impact_qualite": 0.2, "categorie": "cuisine"},
    ],
    "GASTRONOMIQUE": [
        {"nom": "Chef étoilé", "salaire_marche": 4000, "capacite_couverts": 50, "impact_qualite": 1.0, "categorie": "cuisine"},
        {"nom": "Chef", "salaire_marche": 3000, "capacite_couverts": 50, "impact_qualite": 0.9, "categorie": "cuisine"},
        {"nom": "Second de cuisine", "salaire_marche": 2200, "capacite_couverts": 40, "impact_qualite": 0.8, "categorie": "cuisine"},
        {"nom": "Chef de partie", "salaire_marche": 2000, "capacite_couverts": 35, "impact_qualite": 0.7, "categorie": "cuisine"},
        {"nom": "Commis", "salaire_marche": 1600, "capacite_couverts": 25, "impact_qualite": 0.4, "categorie": "cuisine"},
        {"nom": "Plongeur", "salaire_marche": 1500, "capacite_couverts": 20, "impact_qualite": 0.2, "categorie": "cuisine"},
        {"nom": "Maître d'hôtel", "salaire_marche": 2500, "capacite_couverts": 0,  "impact_qualite": 0.9, "categorie": "salle"},
        {"nom": "Sommelier", "salaire_marche": 2400, "capacite_couverts": 0,  "impact_qualite": 0.8, "categorie": "salle"},
        {"nom": "Chef de rang", "salaire_marche": 1800, "capacite_couverts": 20, "impact_qualite": 0.6, "categorie": "salle"},
        {"nom": "Serveur", "salaire_marche": 1600, "capacite_couverts": 20, "impact_qualite": 0.5, "categorie": "salle"},
    ],
}
