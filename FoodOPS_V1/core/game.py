# foodops/core/game.py

from typing import List, Tuple

import numpy as np
from pydantic import BaseModel

from FoodOPS_V1.core.accounting import (
    Ledger,
    month_amortization,
    post_cogs,
    post_depreciation,
    post_loan_payment,
    post_opening,
    post_payroll,
    post_sales,
    post_services_ext,
)
from FoodOPS_V1.core.market import allocate_demand, clamp_capacity
from FoodOPS_V1.domain import Restaurant, Scenario, RestaurantType
from FoodOPS_V1.domain.local import CATALOG_LOCALS
from FoodOPS_V1.ui.affichage import (
    print_balance_sheet,
    print_income_statement,
    print_opening_balance,
    print_resume_financement,
)
from FoodOPS_V1.ui.director_office import bureau_directeur
from FoodOPS_V1.ui.results_view import print_turn_result
from FoodOPS_V1.utils import get_input


class TurnResult(BaseModel):
    """Snapshot des principaux KPI d'un tour pour un restaurant."""

    restaurant_name: str
    tour: int
    clients_attribues: int
    clients_serv: int
    capacity: int
    price_med: float
    ca: float
    cogs: float
    fixed_costs: float
    marketing: float
    rh_cost: float
    funds_start: float
    funds_end: float
    losses: dict


# constantes gameplay


class FinancingPlan(BaseModel):
    """Simple plan de financement retourné par `propose_financing`.

    Champs clés: apports, prêts (banque/BPI), encours, mensualités et cash initial.
    """

    apport: float
    bank_loan: float
    bpi_loan: float
    frais_dossier: float
    bank_monthly: float
    bpi_monthly: float
    bank_outstanding: float
    bpi_outstanding: float
    cash_initial: float


def propose_financing(fonds_price: float, equip_default: float) -> FinancingPlan:
    """Calcule un plan de financement automatique selon des règles fixes.

    Applique les constantes APPORT_FIXE, BANQUE_FIXE, BPI_MAX pour calculer
    les prêts nécessaires, les mensualités et la trésorerie initiale disponible.

    Args:
        fonds_price: Prix du fonds de commerce
        equip_default: Investissement équipement par défaut

    Returns:
        FinancingPlan complet avec tous les montants et mensualités
    """
    APPORT_FIXE = 50_000.0
    BANQUE_FIXE = 250_000.0
    BPI_MAX = 20_000.0
    FRAIS_PCT = 0.03
    TAUX_BANQUE = 0.045  # annuel
    TAUX_BPI = 0.025  # annuel
    DUREE_BANQUE = 60  # mois
    DUREE_BPI = 48  # mois

    besoin_total = fonds_price + equip_default

    apport = APPORT_FIXE
    bank_loan = BANQUE_FIXE
    reste = besoin_total - (apport + bank_loan)

    bpi_loan = max(0.0, min(BPI_MAX, reste))
    frais_dossier = (bank_loan + bpi_loan) * FRAIS_PCT

    # mensualités simples (amortissement constant sur durée, intérêt moyen)
    bank_monthly = (bank_loan / DUREE_BANQUE) + (bank_loan * TAUX_BANQUE / 12)
    bpi_monthly = (bpi_loan / DUREE_BPI) + (bpi_loan * TAUX_BPI / 12)

    cash_initial = apport + bank_loan + bpi_loan - besoin_total - frais_dossier

    return FinancingPlan(
        apport=apport,
        bank_loan=bank_loan,
        bpi_loan=bpi_loan,
        frais_dossier=frais_dossier,
        bank_monthly=bank_monthly,
        bpi_monthly=bpi_monthly,
        bank_outstanding=bank_loan,
        bpi_outstanding=bpi_loan,
        cash_initial=cash_initial,
    )


def initialisation_restaurants() -> List[Restaurant]:
    """Crée interactivement les restaurants joueurs avec financement et comptabilité.

    Saisit le nombre de joueurs, puis pour chaque joueur :
    - Type de restaurant (Fast Food, Bistrot, Gastro)
    - Sélection automatique du local et équipement
    - Calcul du plan de financement
    - Initialisation de la comptabilité avec écriture d'ouverture
    - Affichage du résumé financier et bilan initial

    Returns:
        Liste des restaurants initialisés et prêts à jouer
    """
    restaurants = []
    menus_by_type = Restaurant.get_default_menus_simple()

    # Saisie du nombre de joueurs ici (la CLI n'envoie plus le param)
    nb_joueurs = int(
        get_input(
            input_message="Nombre de joueurs (1-8) : ",
            error_message="⚠️ Saisis un entier entre 1 et 8.",
            fn_validation=lambda x: 1 <= x <= 8,
        )
    )
    for i in range(nb_joueurs):
        print(f"\n— Joueur {i + 1} —")
        print("Types : 1) Fast Food  2) Bistrot  3) GASTRO")
        type = get_input(
            input_message="Type de restaurant : ",
            error_message="⚠️ Choisis 1, 2 ou 3.",
            fn_validation=lambda x: x in (1, 2, 3),
        )

        type_dict = {1: "FAST_FOOD", 2: "BISTRO", 3: "GASTRO"}
        type_resto = type_dict[type]

        # Sélection du local (simple: premier de la liste pour ce type)
        local = CATALOG_LOCALS[0]

        # Équipement par défaut selon type (tu pourras affiner)

        equip_default_dict = {
            "FAST_FOOD": 80_000.0,
            "BISTRO": 120_000.0,
            "Gastro": 180_000.0,
        }
        equip_default = equip_default_dict[type_resto]

        # Plan de financement selon règles admin
        plan = propose_financing(local.prix_fond, equip_default)

        # Création du restaurant
        restaurant = Restaurant(
            name=f"Resto {i + 1}",
            type=RestaurantType[type_resto],
            local=local,
            funds=plan.cash_initial,  # trésorerie après financement - investissement - frais
            equipment_invest=equip_default,
            menu=menus_by_type[RestaurantType[type_resto]],
            notoriety=0.5,
            monthly_bpi=plan.bpi_monthly,
            monthly_bank=plan.bank_monthly,
            bpi_outstanding=plan.bpi_outstanding,
            bank_outstanding=plan.bank_outstanding,
        )

        # Initialiser la compta + écriture d'ouverture
        restaurant.ledger = Ledger()
        total_loans = plan.bank_loan + plan.bpi_loan
        post_opening(
            restaurant.ledger,
            equity=None,  # auto-équilibrage 101
            cash=restaurant.funds,  # tréso initiale
            equipment=restaurant.equipment_invest,  # immobilisations
            loans_total=total_loans,  # dette initiale
        )

        # Résumé financement et bilan d'ouverture
        print_resume_financement(restaurant, plan)
        print_opening_balance(restaurant)

        restaurants.append(restaurant)

    return restaurants


DISPLAY_COMPTA = False


def _sell_from_finished_fifo(
    restaurant: Restaurant, quantity: int
) -> Tuple[int, float]:
    """Vend jusqu'à `quantity` portions depuis l'inventaire produits finis en FIFO.

    Traite l'inventaire par ordre chronologique (premier entré, premier sorti),
    met à jour les quantités en stock et calcule le chiffre d'affaires total.

    Args:
        restaurant: Restaurant avec l'inventaire à traiter
        quantity: Nombre maximum de portions à vendre (doit être >= 0)

    Returns:
        Tuple contenant:
        - int: Nombre total de portions effectivement vendues
        - float: Chiffre d'affaires total généré (arrondi à 2 décimales)

    Note:
        Les lots vides sont automatiquement supprimés de l'inventaire.
        Retourne (0, 0.0) si pas de stock ou quantité invalide.
    """
    inventory = restaurant.inventory

    # Early return if no inventory available or invalid quantity requested
    if not inventory.finished or quantity <= 0:
        return (0, 0.0)

    # Initialize tracking variables
    need = quantity  # Remaining quantity to sell
    sold = 0  # Total portions sold so far
    revenue = 0.0  # Total revenue accumulated
    i = 0  # Current batch index in FIFO queue

    # Process batches in FIFO order until we've sold enough or run out of inventory
    while i < len(inventory.finished) and need > 0:
        # Get current batch from FIFO queue
        batch = inventory.finished[i]

        # Calculate how many portions we can take from this batch
        # Use safe attribute access in case portions attribute is missing
        available_portions = int(getattr(batch, "portions", 0))
        take = min(available_portions, need)

        # Process the sale if we can take any portions from this batch
        if take > 0:
            # Update totals
            sold += take

            # Calculate revenue for this batch using its specific selling price
            # Use safe attribute access with fallback to 0.0 for missing prices
            batch_price = float(getattr(batch, "selling_price", 0.0) or 0.0)
            revenue += take * batch_price

            # Update batch inventory (reduce available portions)
            batch.portions -= take

            # Update remaining need
            need -= take

        # Remove empty batches from inventory or move to next batch
        if getattr(batch, "portions", 0) <= 0:
            # Batch is exhausted, remove it from inventory
            inventory.finished.pop(i)
            # Don't increment i since we removed an element
        else:
            # Batch still has portions, move to next batch
            i += 1

    # Return total sold and revenue (rounded to avoid floating point precision issues)
    return (sold, round(revenue, 2))


def _fixed_costs_of(restaurant: Restaurant) -> float:
    """Calcule les coûts fixes mensuels totaux du restaurant.

    Args:
        restaurant: Restaurant dont calculer les coûts fixes

    Returns:
        Somme du loyer du local et des charges récurrentes mensuelles
    """
    # Somme du loyer du local et des charges récurrentes mensuelles
    return restaurant.local.loyer + restaurant.charges_reccurentes


def _rh_cost_of(restaurant: Restaurant) -> float:
    """Calcule le coût salarial mensuel total de l'équipe.

    Args:
        restaurant: Restaurant avec l'équipe à évaluer

    Returns:
        Somme de tous les salaires totaux de l'équipe, arrondie à 2 décimales
    """
    # Additionne tous les salaires de l'équipe et arrondit à 2 décimales
    return round(sum([employee.salaire_total for employee in restaurant.equipe]), 2)


def _service_minutes_per_cover(rtype: RestaurantType) -> float:
    """Retourne le temps de service standard par couvert selon le type de restaurant.

    Args:
        rtype: Type de restaurant (FAST_FOOD, BISTRO, GASTRO)

    Returns:
        Durée en minutes pour servir un couvert de ce type de restaurant
    """
    # Récupère la durée de service depuis la constante globale selon le type de restaurant
    return float()


def _service_capacity_with_minutes(restaurant: Restaurant, clients_cap: int) -> int:
    """Calcule la capacité de service limitée par les minutes disponibles.

    Args:
        restaurant: Restaurant avec les minutes de service disponibles
        clients_cap: Capacité théorique en nombre de clients

    Returns:
        Capacité effective limitée par le temps de service disponible.
        Retourne la capacité d'entrée si les minutes sont illimitées.
    """
    # Calcule les minutes nécessaires par couvert selon le type de restaurant
    min_per_cover = restaurant.SERVICE_MINUTES_PER_COVER
    # Récupère les minutes de service encore disponibles
    minutes_left = restaurant.service_minutes_left

    # Si minutes illimitées ou temps par couvert invalide, pas de limitation
    if minutes_left == float("inf") or min_per_cover <= 0:
        return clients_cap

    # Retourne le minimum entre la capacité théorique et celle permise par le temps
    return min(minutes_left // min_per_cover, clients_cap)


def _consume_service_minutes(restaurant: Restaurant, clients_served: int) -> None:
    """Consomme les minutes de service nécessaires pour servir les clients.

    Args:
        restaurant: Restaurant dont consommer les minutes de service
        clients_served: Nombre de clients effectivement servis

    Note:
        Appelle la méthode du restaurant si disponible, sinon décrémente directement.
    """
    # Calcule les minutes nécessaires selon le type de restaurant
    min_per_cover = _service_minutes_per_cover(restaurant.type)
    # Calcule le temps total requis pour servir tous les clients
    need = int(round(min_per_cover * max(0, int(clients_served))))

    # Appelle la méthode de consommation du restaurant si elle existe
    restaurant.consume_service_minutes(need)

    # Fallback : décrémente directement l'attribut si présent (pour compatibilité)
    restaurant.service_minutes_left = max(
        0, int(restaurant.service_minutes_left - need)
    )


def _apply_client_losses(
    restaurant: Restaurant,
    demanded: int,
    capacity_rh: int,
    cap_service: int,
    available_finished: int,
    sold: int,
) -> dict:
    """Calcule la répartition des pertes clients et applique une pénalité de notoriété.

    Analyse les causes de perte de clients :
    - manque_stock: capacité existante mais stock insuffisant
    - manque_capacite: limite RH/service avant même le stock
    - autre: arrondis/bruit/débordement vs demande

    Args:
        restaurant: Restaurant à analyser
        demanded: Nombre de clients demandant le service
        capacity_rh: Capacité RH/salle maximale
        cap_service: Capacité limitée par les minutes de service
        available_finished: Stock de produits finis disponible
        sold: Nombre effectivement servi

    Returns:
        Dictionnaire avec la répartition des pertes par cause

    Note:
        Applique une légère pénalité de notoriété basée sur le pourcentage de demande perdue.
    """
    asked = int(max(0, demanded))
    cap_stage = max(
        0, min(asked, int(capacity_rh))
    )  # capacité RH/salle de clamp_capacity
    cap_service_stage = max(
        0, min(cap_stage, int(cap_service))
    )  # borne par minutes de service
    stock_stage = max(
        0, min(cap_service_stage, int(available_finished))
    )  # borne par stock
    served = int(max(0, sold))

    lost_stock = max(0, stock_stage - served)
    lost_capacity = max(
        0, cap_service_stage - stock_stage
    )  # ce que la capacité n'a pas permis avant même le stock
    lost_other = max(
        0, asked - max(served, cap_service_stage)
    )  # bruit/arrondi/demande excédentaire

    total_lost = lost_stock + lost_capacity + lost_other

    # Effet notoriété très doux : -0.02 * %demande perdue (max 10 pts)
    if asked > 0 and total_lost > 0:
        frac = min(1.0, total_lost / asked)
        delta = min(0.10, 0.02 * frac * 100.0)  # 0..0.10
        noto = restaurant.notoriety
        restaurant.notoriety = max(0.0, min(1.0, round(noto * (1.0 - delta), 3)))

    return {
        "lost_total": total_lost,
        "lost_stock": lost_stock,
        "lost_capacity": lost_capacity,
        "lost_other": lost_other,
    }


class Game:
    def __init__(self, restaurants: List[Restaurant], scenario: Scenario):
        """Moteur de jeu principal orchestrant les tours mensuels.

        Args:
            restaurants: Liste des restaurants joueurs
            scenario: Scénario de marché fournissant le contexte de demande
        """
        self.restaurants = restaurants
        self.scenario = scenario
        self.current_tour = 1

    def _show_scenario(self, scenario: Scenario) -> None:
        """Affiche les informations du scénario de marché pour informer le joueur.

        Args:
            scenario: Scénario à afficher avec population et segments

        Note:
            Affichage "best-effort" - gère les attributs manquants sans erreur.
        """
        pop = scenario.population_total
        shares = scenario.segments_share
        if pop and shares:
            print("\n=== Scénario du marché ===")
            print(f"Population mensuelle estimée : {int(pop)}")
            for seg, p in shares.items():
                print(f" - {seg}: {p * 100:.1f}%")
            print("==========================\n")

    def play(self) -> None:
        """Lance la boucle de jeu principale sur tous les tours.

        Cycle de vie par tour :
        1) Nettoyage des produits finis expirés
        2) Reset des minutes RH
        3) Allocation de la demande et limitation de capacité
        4) Limitation par minutes de service et stock fini
        5) Vente FIFO depuis l'inventaire et calcul du résultat opérationnel
        6) Calcul des pertes et application de la pénalité de notoriété
        7) Écritures comptables et flux d'emprunts
        8) Mise à jour de la trésorerie
        """
        # ——— Scénario ———
        self._show_scenario(self.scenario)

        restaurant = self.restaurants[0]
        # ——— Bureau du directeur juste après bilan initial ———
        for restaurant in self.restaurants:
            if restaurant.equipe and restaurant.type:
                print(f"\nOuverture du Bureau du Directeur pour {restaurant.name}")
                # signature historique: (equipe, type_resto)
                type_resto = restaurant.type
                restaurant.equipe = bureau_directeur(restaurant.equipe, type_resto)

        # ——— Boucle de jeu ———
        # Nombre de tours : si ton scenario expose nb_tours, on le prend. Sinon, 12 tours par défaut.
        nb_tours = self.scenario.nb_tours if self.scenario.nb_tours else 12

        while self.current_tour <= nb_tours:
            print(f"\n=== 📅 Tour {self.current_tour}/{nb_tours} ===")

            # 0) Péremption produits finis
            for resto in self.restaurants:
                resto.inventory.cleanup_expired(self.current_tour)

            # Reset minutes RH début de tour (fallback no-op si absent)
            for resto in self.restaurants:
                resto.reset_rh_minutes()

            # 1) Allocation de la demande (via le marché/scénario)
            attrib = allocate_demand(self.restaurants, self.scenario)
            served_cap = clamp_capacity(self.restaurants, attrib)

            # 2) Boucle par restaurant
            for index_restaurant, restaurant in enumerate(self.restaurants):
                # Calcul du prix médian du menu du restaurant
                prix_median_menu = restaurant.compute_median_price()

                # Récupération de l'allocation de demande et contraintes de capacité pour ce restaurant
                clients_demandes = attrib[index_restaurant]
                capacite_max_clients = served_cap[index_restaurant]

                # Application de la contrainte de capacité de service basée sur les minutes de personnel disponibles
                capacite_service_clients = _service_capacity_with_minutes(
                    restaurant, capacite_max_clients
                )

                # Application de la contrainte de stock basée sur les portions finies disponibles
                portions_finies_disponibles = restaurant.get_available_portions()
                clients_reellement_servis = min(
                    clients_demandes,
                    capacite_service_clients,
                    portions_finies_disponibles,
                )

                # --- Calcul des pertes de clients par type de contrainte ---
                clients_perdus_par_stock = max(
                    0,
                    clients_demandes
                    - min(clients_demandes, portions_finies_disponibles),
                )
                clients_perdus_par_capacite = max(
                    0,
                    clients_demandes - min(clients_demandes, capacite_service_clients),
                )
                # Éviter le double comptage : "autre" représente les pertes restantes après contraintes de stock et capacité
                clients_perdus_autres = max(
                    0,
                    clients_demandes
                    - clients_reellement_servis
                    - max(clients_perdus_par_stock, clients_perdus_par_capacite),
                )
                pertes_clients = {
                    "lost_stock": clients_perdus_par_stock,
                    "lost_capacity": clients_perdus_par_capacite,
                    "lost_other": clients_perdus_autres,
                    "lost_total": clients_perdus_par_stock
                    + clients_perdus_par_capacite
                    + clients_perdus_autres,
                }

                # Consommation des minutes de service réelles basée sur les clients servis
                _consume_service_minutes(restaurant, clients_reellement_servis)

                # Exécution des ventes (FIFO depuis l'inventaire de produits finis) - chiffre d'affaires exact
                portions_vendues, chiffre_affaires_total = _sell_from_finished_fifo(
                    restaurant, clients_reellement_servis
                )

                # Calcul des financiers du tour (COGS reconnus au moment de la production)
                cout_marchandises_vendues = float(
                    getattr(restaurant, "turn_cogs", 0.0) or 0.0
                )
                charges_fixes = _fixed_costs_of(restaurant)
                depenses_marketing = float(
                    getattr(restaurant, "marketing_budget", 0.0) or 0.0
                )
                couts_masse_salariale = _rh_cost_of(restaurant)
                tresorerie_debut = float(getattr(restaurant, "funds", 0.0) or 0.0)

                # Résultat opérationnel (hors amortissements/intérêts - postés en comptabilité juste après)
                ventes_totales = float(chiffre_affaires_total)
                resultat_operationnel = (
                    ventes_totales
                    - cout_marchandises_vendues
                    - charges_fixes
                    - depenses_marketing
                    - couts_masse_salariale
                )
                tresorerie_fin = round(tresorerie_debut + resultat_operationnel, 2)

                # Application des pertes de clients (bonus mini)
                pertes_clients = _apply_client_losses(
                    restaurant,
                    demanded=clients_demandes,
                    capacity_rh=capacite_max_clients,
                    cap_service=capacite_service_clients,
                    available_finished=portions_finies_disponibles,
                    sold=portions_vendues,
                )
                # Tu peux logguer rapidement :
                if pertes_clients["lost_total"] > 0:
                    print(
                        f"⚠️ Pertes clients — {restaurant.name}: "
                        f"{pertes_clients['lost_total']} (stock: {pertes_clients['lost_stock']}, "
                        f"capacité: {pertes_clients['lost_capacity']}, autre: {pertes_clients['lost_other']})"
                    )

                # Objet "turn result" minimal pour affichage
                turn_result = TurnResult(
                    restaurant_name=restaurant.name,
                    tour=self.current_tour,
                    clients_attribues=clients_demandes,
                    clients_serv=portions_vendues,
                    capacity=capacite_max_clients,  # pour % capacité utilisée
                    price_med=prix_median_menu,
                    ca=round(chiffre_affaires_total, 2),
                    cogs=round(cout_marchandises_vendues, 2),
                    fixed_costs=round(charges_fixes, 2),
                    marketing=round(depenses_marketing, 2),
                    rh_cost=round(couts_masse_salariale, 2),
                    funds_start=round(tresorerie_debut, 2),
                    funds_end=round(tresorerie_fin, 2),
                    losses=pertes_clients,
                )

                # 3) Affichage gameplay
                print_turn_result(turn_result)

                # 4) COMPTABILISATION (posts standards)
                post_sales(restaurant.ledger, self.current_tour, turn_result.ca)
                post_cogs(restaurant.ledger, self.current_tour, turn_result.cogs)
                post_services_ext(
                    restaurant.ledger,
                    self.current_tour,
                    turn_result.fixed_costs + turn_result.marketing,
                )
                post_payroll(restaurant.ledger, self.current_tour, turn_result.rh_cost)

                # Dotations aux amortissements
                dot = month_amortization(restaurant.equipment_invest)
                post_depreciation(restaurant.ledger, self.current_tour, dot)

                # Emprunts : calcul intérêts / capital du mois
                def split_interest_principal(outstanding, annual_rate, monthly_payment):
                    if monthly_payment <= 0 or outstanding <= 0:
                        return (0.0, 0.0, outstanding)
                    iamt = round(outstanding * (annual_rate / 12.0), 2)
                    pmt_principal = max(0.0, round(monthly_payment - iamt, 2))
                    new_out = max(0.0, round(outstanding - pmt_principal, 2))
                    return (iamt, pmt_principal, new_out)

                # BPI
                i_bpi, p_bpi, restaurant.bpi_outstanding = split_interest_principal(
                    getattr(turn_result, "bpi_outstanding", 0.0),
                    getattr(restaurant, "bpi_rate_annual", 0.0),
                    getattr(restaurant, "monthly_bpi", 0.0),
                )
                post_loan_payment(
                    restaurant.ledger, self.current_tour, i_bpi, p_bpi, "BPI"
                )

                # Banque
                i_bank, p_bank, restaurant.bank_outstanding = split_interest_principal(
                    getattr(restaurant, "bank_outstanding", 0.0),
                    getattr(restaurant, "bank_rate_annual", 0.0),
                    getattr(restaurant, "monthly_bank", 0.0),
                )
                post_loan_payment(
                    restaurant.ledger, self.current_tour, i_bank, p_bank, "Banque"
                )

                # Mise à jour trésorerie gameplay (après flux financiers)
                restaurant.funds = round(
                    tr.funds_end - (i_bpi + p_bpi + i_bank + p_bank), 2
                )

                # Reset COGS de production (on l'a reconnu ce tour)
                restaurant.turn_cogs = 0.0

                # Mise à jour satisfaction RH selon l'utilisation (si présent)
                if hasattr(restaurant, "update_rh_satisfaction"):
                    try:
                        restaurant.update_rh_satisfaction()
                    except Exception:
                        pass

                # 5) AFFICHAGE COMPTA (si présent)
                if DISPLAY_COMPTA:
                    bal_mtd = restaurant.ledger.balance_accounts(
                        upto_tour=self.current_tour
                    )
                    print_income_statement(
                        bal_mtd,
                        title=f"Compte de résultat — {restaurant.name} — cumul à T{self.current_tour}",
                    )
                    print_balance_sheet(
                        bal_mtd,
                        title=f"Bilan — {restaurant.name} — à T{self.current_tour}",
                    )

            self.current_tour += 1
