# Paramètres financiers (admin/scénario)

from FoodOPS_V1.domain.restaurant import RestaurantType

# --- Règles d'équipement (automatique) ---
# Montant de base par concept, multiplié par un facteur propre au local.
EQUIP_BASE_BY_TYPE = {
    RestaurantType.FAST_FOOD: 15000.0,
    RestaurantType.BISTRO: 30000.0,
    RestaurantType.GASTRO: 50000.0,
}

# --- Apport & prêts (fixes) ---
ADMIN_EQUITY = 50000.0  # Apport donné à chaque joueur
BANK_FIXED_AMOUNT = 250000.0  # Prêt bancaire (fixe)
BPI_MAX_AMOUNT = 20000.0  # BPI (plafond), accordé d'office jusque ce max

# --- Taux & durées ---
BPI_RATE_ANNUAL = 0.00  # 0%/an
BPI_YEARS = 5  # 60 mois
BANK_RATE_ANNUAL = 0.03  # 3%/an
BANK_YEARS = 7  # 84 mois

# --- Frais & overheads ---
INSTALL_COST_RATE = 0.03  # frais d'installation (% de l'investissement)
FIXED_OVERHEADS = {
    "assurance": 120.0,
    "abonnements": 180.0,
}
