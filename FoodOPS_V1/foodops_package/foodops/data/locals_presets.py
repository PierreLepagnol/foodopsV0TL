# foodops/data/locals_presets.py
# -*- coding: utf-8 -*-
from ..domain.local import Local

# Locaux de départ par type
DEFAULT_LOCALS = {
    "FAST_FOOD": [
        Local(nom="Kiosque Campus",   surface=50.0, capacite_clients=40, loyer=2200.0, prix_fond=140_000.0, visibilite=1.1),
        Local(nom="Galerie Marchande", surface=80.0, capacite_clients=80, loyer=4500.0, prix_fond=270_000.0, visibilite=1.3),
    ],
    "BISTRO": [
        Local(nom="Angle République",  surface=60.0, capacite_clients=40, loyer=2500.0, prix_fond=200_000.0, visibilite=1.1),
        Local(nom="Centre ville",      surface=100.0, capacite_clients=80, loyer=5200.0, prix_fond=260_000.0, visibilite=1.3),
    ],
    "GASTRO": [
        Local(nom="Local en périphérie", surface=70.0, capacite_clients=30, loyer=3000.0, prix_fond=300_000.0, visibilite=1.4),
        Local(nom="Quartier Chic",     surface=90.0, capacite_clients=70, loyer=12000.0, prix_fond=400_000.0, visibilite=1.5),
    ],
}
