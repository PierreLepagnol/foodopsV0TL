# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import List, Tuple

from ..domain import Restaurant
from ..core.turn import allocate_demand, clamp_capacity, menu_price_median
from foodops.ui.director_office import bureau_directeur  # garde ta signature actuelle
from ..core.accounting import (
    month_amortization, post_sales, post_cogs, post_services_ext,
    post_payroll, post_depreciation, post_loan_payment
)
from ..ui.results_view import print_turn_result

# Si ton projet expose un scénario par défaut :
try:
    from ..data.scenario_presets import get_default_scenario, Scenario
except Exception:
    get_default_scenario = None
    Scenario = None

# Comptes “stylés” selon ta version d’UI (si tu as un print_* avec signature différente, adapte ici)
try:
    from ..ui.accounting_view import print_income_statement, print_balance_sheet
    HAS_ACCT_VIEWS = True
except Exception:
    HAS_ACCT_VIEWS = False


# --------- Helpers internes ---------

def _sell_from_finished_fifo(resto: Restaurant, qty: int) -> Tuple[int, float]:
    """
    Vend jusqu'à `qty` portions depuis les lots de produits finis (FIFO),
    met à jour l'inventaire, et renvoie (vendu, chiffre_d_affaires).
    """
    inv = getattr(resto, "inventory", None)
    if inv is None or not inv.finished or qty <= 0:
        return (0, 0.0)

    need = qty
    sold = 0
    revenue = 0.0
    i = 0
    while i < len(inv.finished) and need > 0:
        b = inv.finished[i]
        take = min(b.portions, need)
        if take > 0:
            sold += take
            revenue += take * float(b.selling_price)
            b.portions -= take
            need -= take

        if b.portions <= 0:
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


@dataclass
class Game:
    restaurants: List[Restaurant]
    # Si tu as encore un DefaultScenario “legacy”, on le garde en field — mais on utilisera scenario_presets s’il existe.
    scenario: object = field(default_factory=lambda: None)
    current_tour: int = 1

    def _show_scenario(self, sc) -> None:
        try:
            pop = getattr(sc, "population_total", None)
            shares = getattr(sc, "segments_share", None)
            if pop and shares:
                print("\n=== Scénario du marché ===")
                print(f"Population mensuelle estimée : {int(pop)}")
                for seg, p in shares.items():
                    print(f" - {seg}: {p*100:.1f}%")
                print("==========================\n")
        except Exception:
            pass  # affichage best-effort

    def play(self) -> None:
        # ——— Scénario ———
        scenario = None
        if get_default_scenario:
            scenario = get_default_scenario()
            self._show_scenario(scenario)

        # ——— Bureau du directeur juste après bilan initial ———
        for r in self.restaurants:
            if hasattr(r, "equipe") and hasattr(r, "type_resto"):
                print(f"\nOuverture du Bureau du Directeur pour {r.name}")
                # si ta version de bureau_directeur accepte (resto, current_tour), adapte ici :
                r.equipe = bureau_directeur(r.equipe, r.type_resto)

        # ——— Boucle de jeu ———
        # Nombre de tours : si ton scenario expose nb_tours, on le prend. Sinon, 12 tours par défaut.
        nb_tours = getattr(self.scenario, "nb_tours", None)
        if nb_tours is None:
            nb_tours = getattr(scenario, "nb_tours", 12) if scenario else 12

        while self.current_tour <= nb_tours:
            print(f"\n=== 📅 Tour {self.current_tour}/{nb_tours} ===")

            # 0) Péremption produits finis au début du tour
            for r in self.restaurants:
                inv = getattr(r, "inventory", None)
                if inv:
                    inv.cleanup_expired(self.current_tour)

            # 1) Allocation de la demande (via le marché/scénario)
            if scenario is not None:
                attrib = allocate_demand(self.restaurants, scenario)
            else:
                # fallback si tu n'as pas (encore) le module scenario_presets
                demand = getattr(self.scenario, "demand_per_tour", 1000) if self.scenario else 1000
                # on “simule” un mini-scenario : tout le monde même panier/besoin
                fake = {i: int(demand / max(1, len(self.restaurants))) for i in range(len(self.restaurants))}
                attrib = fake

            served_cap = clamp_capacity(self.restaurants, attrib)

            # 2) Boucle par restaurant
            for i, r in enumerate(self.restaurants):
                price_med = menu_price_median(r)

                # Demande attribuée & capacité “RH/tempo” déjà bornée
                clients_attr = int(attrib.get(i, 0))
                clients_cap = int(served_cap.get(i, 0))

                # Nouveau : limite **finale** par stock de produits finis (FIFO + CA exact)
                inv = getattr(r, "inventory", None)
                finished_avail = inv.total_finished_portions() if inv else 0
                ask = min(clients_cap, finished_avail)
                sold, revenue = _sell_from_finished_fifo(r, ask)

                # Comptes du tour (reconnaissance COGS à la production)
                cogs = float(getattr(r, "turn_cogs", 0.0) or 0.0)
                fixed_costs = _fixed_costs_of(r)
                marketing = float(getattr(r, "marketing_budget", 0.0) or 0.0)
                rh_cost = _rh_cost_of(r)
                funds_start = float(getattr(r, "funds", 0.0) or 0.0)

                # Résultat opérationnel (hors amort./intérêts — qui sont postés en compta juste après)
                ca = float(revenue)
                op_result = ca - cogs - fixed_costs - marketing - rh_cost
                funds_end = round(funds_start + op_result, 2)

                # Objet “turn result” minimal pour affichage (on évite ici les dépendances rigides)
                tr = SimpleNamespace(
                    restaurant_name=r.name,
                    tour=self.current_tour,
                    clients_attr=clients_attr,
                    clients_serv=sold,
                    capacity=clients_cap,            # pour % capacité utilisée
                    price_med=price_med,
                    ca=round(ca, 2),
                    cogs=round(cogs, 2),
                    fixed_costs=round(fixed_costs, 2),
                    marketing=round(marketing, 2),
                    rh_cost=round(rh_cost, 2),
                    funds_start=round(funds_start, 2),
                    funds_end=round(funds_end, 2),
                )

                # 3) Affichage gameplay
                print_turn_result(tr)

                # 4) COMPTABILISATION (posts standards)
                post_sales(r.ledger, self.current_tour, tr.ca)
                post_cogs(r.ledger, self.current_tour, tr.cogs)
                post_services_ext(r.ledger, self.current_tour, tr.fixed_costs + tr.marketing)
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
                    r.bpi_outstanding, r.bpi_rate_annual, r.monthly_bpi
                )
                post_loan_payment(r.ledger, self.current_tour, i_bpi, p_bpi, "BPI")

                # Banque
                i_bank, p_bank, r.bank_outstanding = split_interest_principal(
                    r.bank_outstanding, r.bank_rate_annual, r.monthly_bank
                )
                post_loan_payment(r.ledger, self.current_tour, i_bank, p_bank, "Banque")

                # Mise à jour trésorerie gameplay (après flux financiers)
                r.funds = round(tr.funds_end - (i_bpi + p_bpi + i_bank + p_bank), 2)

                # Reset COGS de production (on l’a reconnu ce tour)
                r.turn_cogs = 0.0

                # 5) AFFICHAGE COMPTA (si présent)
                if HAS_ACCT_VIEWS:
                    bal_mtd = r.ledger.balance_accounts(upto_tour=self.current_tour)
                    print_income_statement(
                        bal_mtd,
                        title=f"Compte de résultat — {r.name} — cumul à T{self.current_tour}"
                    )
                    print_balance_sheet(
                        bal_mtd,
                        title=f"Bilan — {r.name} — à T{self.current_tour}"
                    )

            self.current_tour += 1
