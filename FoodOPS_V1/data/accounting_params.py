"""
Paramètres comptables FR (simplifiés, hors TVA pour l'instant).
"""

# Amortissement linéaire des équipements (années)
EQUIP_AMORT_YEARS = 5

# Comptes (PCG simplifié)
ACCOUNTS = {
    # Actif
    "512": "Banque",
    "215": "Installations techniques, matériel et outillage (brut)",
    "2815": "Amortissements du matériel (cumul)",
    # Passif
    "101": "Capitaux propres",
    "164": "Emprunts auprès des établissements de crédit",
    # Charges d'exploitation
    "70": "Ventes de produits finis (CA)",
    "60": "Achats consommés (COGS)",
    "61": "Services extérieurs (loyer, marketing, abonnements, etc.)",
    "64": "Charges de personnel (salaires + charges patronales)",
    "681": "Dotations aux amortissements",
    # Charges financières
    "66": "Charges financières (intérêts)",
}
