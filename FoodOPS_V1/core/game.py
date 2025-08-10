# foodops/core/game.py

from typing import Dict, List, Tuple

import numpy as np

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
from FoodOPS_V1.core.finance import propose_financing
from FoodOPS_V1.core.market import allocate_demand, clamp_capacity
from FoodOPS_V1.domain import Restaurant, Scenario
from FoodOPS_V1.domain.local import CATALOG_LOCALS
from FoodOPS_V1.domain.recipe import SimpleRecipe
from FoodOPS_V1.domain.types import RestaurantType, TurnResult
from FoodOPS_V1.rules.recipe_factory import build_menu_for_type
from FoodOPS_V1.ui.affichage import (
    print_opening_balance,
    print_resume_financement,
    print_income_statement,
    print_balance_sheet,
)
from FoodOPS_V1.ui.director_office import bureau_directeur
from FoodOPS_V1.ui.results_view import print_turn_result
from FoodOPS_V1.utils import get_input

# Simulation


def get_default_menus_simple() -> Dict[RestaurantType, List[SimpleRecipe]]:
    return {
        RestaurantType.FAST_FOOD: build_menu_for_type(RestaurantType.FAST_FOOD),
        RestaurantType.BISTRO: build_menu_for_type(RestaurantType.BISTRO),
        RestaurantType.GASTRO: build_menu_for_type(RestaurantType.GASTRO),
    }


def initialisation_restaurants() -> List[Restaurant]:
    """Interactively create restaurants and post opening entries.

    Returns a list of initialized `Restaurant` instances with:
    - default menus
    - initial financing plan and cash
    - opening accounting entry
    """
    restaurants = []
    menus_by_type = get_default_menus_simple()

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

# Temps de service par couvert (minutes)
SERVICE_MIN_PER_COVER = {
    RestaurantType.FAST_FOOD: 1.5,  # prise de commande + délivrance
    RestaurantType.BISTRO: 4.0,
    RestaurantType.GASTRO: 7.0,
}

# --------- Helpers internes ---------


def _sell_from_finished_fifo(restaurant: Restaurant, quatity: int) -> Tuple[int, float]:
    """
    Sell up to `quatity` portions from finished goods inventory using FIFO (First In, First Out) method.

    This function processes the restaurant's finished goods inventory in chronological order,
    selling the oldest items first. It updates the inventory quantities in-place and calculates
    the total revenue based on each batch's selling price.

    Args:
        resto: Restaurant object containing the inventory to sell from
        quatity: Maximum number of portions to sell (must be >= 0)

    Returns:
        Tuple containing:
        - int: Total number of portions actually sold
        - float: Total revenue generated from sales (rounded to 2 decimal places)

    Note:
        - If no finished goods are available or quatity <= 0, returns (0, 0.0)
        - Batches with 0 portions are automatically removed from inventory
        - Uses safe attribute access with getattr() for robustness
    """
    inventory = restaurant.inventory

    # Early return if no inventory available or invalid quantity requested
    if not inventory.finished or quatity <= 0:
        return (0, 0.0)

    # Initialize tracking variables
    need = quatity  # Remaining quantity to sell
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
    """Retourne les coûts fixes mensuels (loyer + autres charges) d'un restaurant."""
    # Somme du loyer du local et des charges récurrentes mensuelles
    return restaurant.local.loyer + restaurant.charges_reccurentes


def _rh_cost_of(restaurant: Restaurant) -> float:
    """Calcule le coût salarial mensuel total à partir des objets `equipe` exposant `salaire_total`."""
    # Additionne tous les salaires de l'équipe et arrondit à 2 décimales
    return round(sum([employee.salaire_total for employee in restaurant.equipe]), 2)


def _service_minutes_per_cover(rtype: RestaurantType) -> float:
    """Retourne le temps de service nominal par couvert pour le type de concept donné."""
    # Récupère la durée de service depuis la constante globale selon le type de restaurant
    return float(SERVICE_MIN_PER_COVER[rtype])


def _service_capacity_with_minutes(restaurant: Restaurant, clients_cap: int) -> int:
    """Retourne la capacité finale limitée par les minutes de service restantes.

    Comportement de repli : si des attributs manquent, retourne la capacité d'entrée.
    """
    # Calcule les minutes nécessaires par couvert selon le type de restaurant
    min_per_cover = _service_minutes_per_cover(restaurant.type)
    # Récupère les minutes de service encore disponibles
    minutes_left = float(restaurant.service_minutes_left)

    # Si minutes illimitées ou temps par couvert invalide, pas de limitation
    if minutes_left == float("inf") or min_per_cover <= 0:
        return int(clients_cap)

    # Retourne le minimum entre la capacité théorique et celle permise par le temps
    return int(min(minutes_left // min_per_cover, clients_cap))


def _consume_service_minutes(restaurant: Restaurant, clients_served: int) -> None:
    """Consomme les minutes de service si disponibles, sinon ne fait rien."""
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


def _finished_available(restaurant: Restaurant) -> int:
    inventory = restaurant.inventory
    if inventory.total_finished_portions:
        return int(inventory.total_finished_portions())
    # fallback ultra-simple : pas de produits finis → 0
    return 0


def _apply_client_losses(
    restaurant: Restaurant,
    demanded: int,
    capacity_rh: int,
    cap_service: int,
    available_finished: int,
    sold: int,
) -> dict:
    """Compute a simple breakdown of customer losses for this turn.

    - manque_stock: capacity existed but finished stock was insufficient
    - manque_capacite: RH/tempo limit before even considering stock
    - autre: rounding/noise/overflow vs demand

    Also applies a tiny notoriety penalty based on lost share, clamped to [0..1].
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
        """Main game engine orchestrating monthly turns.

        - restaurants: list of player restaurants
        - scenario: market scenario providing demand context
        """
        self.restaurants = restaurants
        self.scenario = scenario
        self.current_tour = 1

    def _show_scenario(self, scenario: Scenario) -> None:
        """Best-effort scenario display to inform the player before starting."""
        pop = scenario.population_total
        shares = scenario.segments_share
        if pop and shares:
            print("\n=== Scénario du marché ===")
            print(f"Population mensuelle estimée : {int(pop)}")
            for seg, p in shares.items():
                print(f" - {seg}: {p * 100:.1f}%")
            print("==========================\n")

    def play(self) -> None:
        """Run the game loop across all turns.

        Lifecycle per turn:
        1) cleanup expired finished goods
        2) reset RH minutes
        3) allocate demand and clamp capacity
        4) bound by service minutes and finished stock
        5) sell FIFO from inventory and compute op result
        6) compute losses and apply tiny notoriety penalty
        7) post accounting entries and loan flows
        8) update funds
        """
        # ——— Scénario ———
        self._show_scenario(self.scenario)

        restaurant = self.restaurants[0]
        # ——— Bureau du directeur juste après bilan initial ———
        for restaurant in self.restaurants:
            if hasattr(restaurant, "equipe") and hasattr(restaurant, "type"):
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
            if self.scenario is not None:
                attrib = allocate_demand(self.restaurants, self.scenario)
            else:
                # Fallback distribution if no scenario is provided
                demand = (
                    self.scenario.demand_per_tour
                    if self.scenario.demand_per_tour
                    else 1000
                )
                # Répartition uniforme simple (non utilisée par défaut)
                attrib = {
                    i: int(demand / max(1, len(self.restaurants)))
                    for i in range(len(self.restaurants))
                }

            served_cap = clamp_capacity(self.restaurants, attrib)

            # 2) Boucle par restaurant
            for i, restaurant in enumerate(self.restaurants):
                # Select items from menu
                # Compute median price of menu
                menu = restaurant.menu

                prix_des_items = [item.price for item in menu if item is not None]
                price_med = np.median(prix_des_items) if prix_des_items else 0.0

                clients_attr = int(attrib.get(i, 0))
                clients_cap = int(served_cap.get(i, 0))

                # Capacité bornée par minutes de service disponibles (serveur·euse·s)
                clients_serv_cap = _service_capacity_with_minutes(
                    restaurant, clients_cap
                )

                # Limite par stock de produits finis
                finished_avail = _finished_available(restaurant)
                target_serv = min(clients_attr, clients_serv_cap, finished_avail)

                # --- Calcul pertes clients ---
                lost_stock = max(0, clients_attr - min(clients_attr, finished_avail))
                lost_capacity = max(
                    0, clients_attr - min(clients_attr, clients_serv_cap)
                )
                # On évite double comptage : "other" = reste après stock et capacité
                lost_other = max(
                    0,
                    clients_attr - target_serv - max(lost_stock, lost_capacity),
                )
                losses = {
                    "lost_stock": lost_stock,
                    "lost_capacity": lost_capacity,
                    "lost_other": lost_other,
                    "lost_total": lost_stock + lost_capacity + lost_other,
                }

                # Consommer minutes de service réelles
                _consume_service_minutes(restaurant, target_serv)

                # Ventes (FIFO produits finis) — CA exact
                sold, revenue = _sell_from_finished_fifo(restaurant, target_serv)

                # Comptes du tour (COGS reconnus à la production)
                cogs = float(getattr(restaurant, "turn_cogs", 0.0) or 0.0)
                fixed_costs = _fixed_costs_of(restaurant)
                marketing = float(getattr(restaurant, "marketing_budget", 0.0) or 0.0)
                rh_cost = _rh_cost_of(restaurant)
                funds_start = float(getattr(restaurant, "funds", 0.0) or 0.0)

                # Résultat opé (hors amort./intérêts — postés en compta juste après)
                ca = float(revenue)
                op_result = ca - cogs - fixed_costs - marketing - rh_cost
                funds_end = round(funds_start + op_result, 2)

                # Pertes de clients (bonus mini)
                losses = _apply_client_losses(
                    restaurant,
                    demanded=clients_attr,
                    capacity_rh=clients_cap,
                    cap_service=clients_serv_cap,
                    available_finished=finished_avail,
                    sold=sold,
                )
                # Tu peux logguer rapidement :
                if losses["lost_total"] > 0:
                    print(
                        f"⚠️ Pertes clients — {restaurant.name}: "
                        f"{losses['lost_total']} (stock: {losses['lost_stock']}, "
                        f"capacité: {losses['lost_capacity']}, autre: {losses['lost_other']})"
                    )

                # Objet “turn result” minimal pour affichage
                tr = TurnResult(
                    restaurant_name=restaurant.name,
                    tour=self.current_tour,
                    clients_attr=clients_attr,
                    clients_serv=sold,
                    capacity=clients_cap,  # pour % capacité utilisée
                    price_med=price_med,
                    ca=round(ca, 2),
                    cogs=round(cogs, 2),
                    fixed_costs=round(fixed_costs, 2),
                    marketing=round(marketing, 2),
                    rh_cost=round(rh_cost, 2),
                    funds_start=round(funds_start, 2),
                    funds_end=round(funds_end, 2),
                    losses=losses,
                )

                # 3) Affichage gameplay
                print_turn_result(tr)

                # 4) COMPTABILISATION (posts standards)
                post_sales(restaurant.ledger, self.current_tour, tr.ca)
                post_cogs(restaurant.ledger, self.current_tour, tr.cogs)
                post_services_ext(
                    restaurant.ledger, self.current_tour, tr.fixed_costs + tr.marketing
                )
                post_payroll(restaurant.ledger, self.current_tour, tr.rh_cost)

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
                    getattr(restaurant, "bpi_outstanding", 0.0),
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
