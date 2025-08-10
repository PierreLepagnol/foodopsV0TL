# foodops/core/game.py

from types import SimpleNamespace
from typing import List, Tuple

import numpy as np

from FoodOPS_V1.domain import Restaurant, RestaurantType, Scenario
from FoodOPS_V1.core.market import (
    allocate_demand,
    clamp_capacity,
)
from FoodOPS_V1.ui.director_office import (
    bureau_directeur,
)  # garde ta signature actuelle
from FoodOPS_V1.core.accounting import (
    month_amortization,
    post_sales,
    post_cogs,
    post_services_ext,
    post_payroll,
    post_depreciation,
    post_loan_payment,
)
from FoodOPS_V1.ui.results_view import print_turn_result

# from FoodOPS_V1.domain.scenario import get_default_scenario

from FoodOPS_V1.ui.accounting_view import (
    print_income_statement,
    print_balance_sheet,
)

HAS_ACCT_VIEWS = True


# Temps de service par couvert (minutes)
SERVICE_MIN_PER_COVER = {
    RestaurantType.FAST_FOOD: 1.5,  # prise de commande + délivrance
    RestaurantType.BISTRO: 4.0,
    RestaurantType.GASTRO: 7.0,
}

# --------- Helpers internes ---------


def _sell_from_finished_fifo(resto: Restaurant, qty: int) -> Tuple[int, float]:
    """
    Vend jusqu'à `qty` portions depuis les lots de produits finis (FIFO),
    met à jour l'inventaire, et renvoie (vendu, chiffre_d_affaires).
    """
    inv = getattr(resto, "inventory", None)
    if inv is None or not getattr(inv, "finished", None) or qty <= 0:
        return (0, 0.0)

    need = qty
    sold = 0
    revenue = 0.0
    i = 0
    while i < len(inv.finished) and need > 0:
        b = inv.finished[i]
        take = min(int(getattr(b, "portions", 0)), need)
        if take > 0:
            sold += take
            revenue += take * float(getattr(b, "selling_price", 0.0) or 0.0)
            b.portions -= take
            need -= take

        if getattr(b, "portions", 0) <= 0:
            inv.finished.pop(i)
        else:
            i += 1

    return (sold, round(revenue, 2))


def _fixed_costs_of(resto: Restaurant) -> float:
    od = getattr(resto, "overheads", {}) or {}
    return float(od.get("loyer", 0.0)) + float(od.get("autres", 0.0))


def _rh_cost_of(resto: Restaurant) -> float:
    equipe = getattr(resto, "equipe", []) or []
    total = 0.0
    for emp in equipe:
        total += float(getattr(emp, "salaire_total", 0.0))
    return round(total, 2)


def _service_minutes_per_cover(rtype: RestaurantType) -> float:
    return float(SERVICE_MIN_PER_COVER.get(rtype, 3.0))


def _service_capacity_with_minutes(resto: Restaurant, clients_cap: int) -> int:
    """
    Capacité finale bornée par les minutes de service restantes.
    Fallback doux : si l'attribut n'existe pas, on ne borne pas.
    """
    min_per_cover = _service_minutes_per_cover(
        getattr(resto, "type", RestaurantType.BISTRO)
    )
    minutes_left = float(getattr(resto, "service_minutes_left", float("inf")))
    if minutes_left == float("inf") or min_per_cover <= 0:
        return int(clients_cap)
    return int(min(minutes_left // min_per_cover, clients_cap))


def _consume_service_minutes(resto: Restaurant, clients_served: int) -> None:
    """Consomme des minutes de service si le resto expose l'attribut/méthode ; sinon no-op."""
    min_per_cover = _service_minutes_per_cover(
        getattr(resto, "type", RestaurantType.BISTRO)
    )
    need = int(round(min_per_cover * max(0, int(clients_served))))
    if hasattr(resto, "consume_service_minutes"):
        try:
            resto.consume_service_minutes(need)
            return
        except Exception:
            pass
    # fallback : décrémente un attribut si présent
    if hasattr(resto, "service_minutes_left"):
        try:
            resto.service_minutes_left = max(
                0, int(getattr(resto, "service_minutes_left") - need)
            )
        except Exception:
            pass


def _reset_rh_minutes_if_any(resto: Restaurant) -> None:
    if hasattr(resto, "reset_rh_minutes"):
        try:
            resto.reset_rh_minutes()
        except Exception:
            pass


def _cleanup_expired(resto: Restaurant, current_tour: int) -> None:
    inv = getattr(resto, "inventory", None)
    if inv and hasattr(inv, "cleanup_expired"):
        try:
            inv.cleanup_expired(current_tour)
        except Exception:
            pass


def _finished_available(resto: Restaurant) -> int:
    inv = getattr(resto, "inventory", None)
    if inv and hasattr(inv, "total_finished_portions"):
        try:
            return int(inv.total_finished_portions())
        except Exception:
            return 0
    # fallback ultra-simple : pas de produits finis → 0
    return 0


def _apply_client_losses(
    resto: Restaurant,
    demanded: int,
    cap_rh: int,
    cap_service: int,
    available_finished: int,
    sold: int,
) -> dict:
    """
    Calcule un breakdown des pertes de clients ce tour (pure info + léger effet notoriété).
    - manque_stock : on avait la capacité mais pas le stock produit
    - manque_capacite : RH/tempo (min(cap_service, demanded) limité avant stock)
    - autre : bruit / arrondi

    Renvoie un dict avec détails et applique un micro-malus sur la notoriété (clampé [0..1]).
    """
    asked = int(max(0, demanded))
    cap_stage = max(0, min(asked, int(cap_rh)))  # capacité RH/salle de clamp_capacity
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
        try:
            noto = float(getattr(resto, "notoriety", 0.5))
            resto.notoriety = max(0.0, min(1.0, round(noto * (1.0 - delta), 3)))
        except Exception:
            pass

    return {
        "lost_total": total_lost,
        "lost_stock": lost_stock,
        "lost_capacity": lost_capacity,
        "lost_other": lost_other,
    }


class Game:
    def __init__(self, restaurants: List[Restaurant], scenario: Scenario):
        self.restaurants = restaurants
        self.scenario = scenario
        self.current_tour = 1

    def _show_scenario(self, sc) -> None:
        try:
            pop = getattr(sc, "population_total", None)
            shares = getattr(sc, "segments_share", None)
            if pop and shares:
                print("\n=== Scénario du marché ===")
                print(f"Population mensuelle estimée : {int(pop)}")
                for seg, p in shares.items():
                    print(f" - {seg}: {p * 100:.1f}%")
                print("==========================\n")
        except Exception:
            pass  # affichage best-effort

    def play(self) -> None:
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
            for r in self.restaurants:
                _cleanup_expired(r, self.current_tour)

            # Reset minutes RH début de tour (fallback no-op si absent)
            for r in self.restaurants:
                _reset_rh_minutes_if_any(r)

            # 1) Allocation de la demande (via le marché/scénario)
            if self.scenario is not None:
                attrib = allocate_demand(self.restaurants, self.scenario)
            else:
                demand = (
                    getattr(self.scenario, "demand_per_tour", 1000)
                    if self.scenario
                    else 1000
                )
                fake = {
                    i: int(demand / max(1, len(self.restaurants)))
                    for i in range(len(self.restaurants))
                }
                attrib = fake

            served_cap = clamp_capacity(self.restaurants, attrib)

            # 2) Boucle par restaurant
            for i, r in enumerate(self.restaurants):
                # Select items from menu
                # Compute median price of menu
                menu = r.menu if hasattr(r, "menu") else []
                prix_des_items = [item.price for item in menu if item is not None]
                price_med = np.median(prix_des_items) if prix_des_items else 0.0

                clients_attr = int(attrib.get(i, 0))
                clients_cap = int(served_cap.get(i, 0))

                # Capacité bornée par minutes de service disponibles (serveur·euse·s)
                clients_serv_cap = _service_capacity_with_minutes(r, clients_cap)

                # Limite par stock de produits finis
                finished_avail = _finished_available(r)
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
                _consume_service_minutes(r, target_serv)

                # Ventes (FIFO produits finis) — CA exact
                sold, revenue = _sell_from_finished_fifo(r, target_serv)

                # Comptes du tour (COGS reconnus à la production)
                cogs = float(getattr(r, "turn_cogs", 0.0) or 0.0)
                fixed_costs = _fixed_costs_of(r)
                marketing = float(getattr(r, "marketing_budget", 0.0) or 0.0)
                rh_cost = _rh_cost_of(r)
                funds_start = float(getattr(r, "funds", 0.0) or 0.0)

                # Résultat opé (hors amort./intérêts — postés en compta juste après)
                ca = float(revenue)
                op_result = ca - cogs - fixed_costs - marketing - rh_cost
                funds_end = round(funds_start + op_result, 2)

                # Pertes de clients (bonus mini)
                losses = _apply_client_losses(
                    r,
                    demanded=clients_attr,
                    cap_rh=clients_cap,
                    cap_service=clients_serv_cap,
                    available_finished=finished_avail,
                    sold=sold,
                )
                # Tu peux logguer rapidement :
                if losses["lost_total"] > 0:
                    print(
                        f"  ⚠️  Pertes clients — {r.name}: "
                        f"{losses['lost_total']} (stock:{losses['lost_stock']}, "
                        f"capacité:{losses['lost_capacity']}, autre:{losses['lost_other']})"
                    )

                # Objet “turn result” minimal pour affichage
                tr = SimpleNamespace(
                    restaurant_name=r.name,
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
                post_sales(r.ledger, self.current_tour, tr.ca)
                post_cogs(r.ledger, self.current_tour, tr.cogs)
                post_services_ext(
                    r.ledger, self.current_tour, tr.fixed_costs + tr.marketing
                )
                post_payroll(r.ledger, self.current_tour, tr.rh_cost)

                # Dotations aux amortissements
                dot = month_amortization(r.equipment_invest)
                post_depreciation(r.ledger, self.current_tour, dot)

                # Emprunts : calcul intérêts / capital du mois
                def split_interest_principal(outstanding, annual_rate, monthly_payment):
                    if monthly_payment <= 0 or outstanding <= 0:
                        return (0.0, 0.0, outstanding)
                    iamt = round(outstanding * (annual_rate / 12.0), 2)
                    pmt_principal = max(0.0, round(monthly_payment - iamt, 2))
                    new_out = max(0.0, round(outstanding - pmt_principal, 2))
                    return (iamt, pmt_principal, new_out)

                # BPI
                i_bpi, p_bpi, r.bpi_outstanding = split_interest_principal(
                    getattr(r, "bpi_outstanding", 0.0),
                    getattr(r, "bpi_rate_annual", 0.0),
                    getattr(r, "monthly_bpi", 0.0),
                )
                post_loan_payment(r.ledger, self.current_tour, i_bpi, p_bpi, "BPI")

                # Banque
                i_bank, p_bank, r.bank_outstanding = split_interest_principal(
                    getattr(r, "bank_outstanding", 0.0),
                    getattr(r, "bank_rate_annual", 0.0),
                    getattr(r, "monthly_bank", 0.0),
                )
                post_loan_payment(r.ledger, self.current_tour, i_bank, p_bank, "Banque")

                # Mise à jour trésorerie gameplay (après flux financiers)
                r.funds = round(tr.funds_end - (i_bpi + p_bpi + i_bank + p_bank), 2)

                # Reset COGS de production (on l'a reconnu ce tour)
                r.turn_cogs = 0.0

                # Mise à jour satisfaction RH selon l'utilisation (si présent)
                if hasattr(r, "update_rh_satisfaction"):
                    try:
                        r.update_rh_satisfaction()
                    except Exception:
                        pass

                # 5) AFFICHAGE COMPTA (si présent)
                if HAS_ACCT_VIEWS:
                    bal_mtd = r.ledger.balance_accounts(upto_tour=self.current_tour)
                    print_income_statement(
                        bal_mtd,
                        title=f"Compte de résultat — {r.name} — cumul à T{self.current_tour}",
                    )
                    print_balance_sheet(
                        bal_mtd,
                        title=f"Bilan — {r.name} — à T{self.current_tour}",
                    )

            self.current_tour += 1
