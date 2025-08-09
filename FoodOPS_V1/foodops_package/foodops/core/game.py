# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List
from ..domain import Restaurant
from ..scenarios.default import DefaultScenario
from ..core.turn import allocate_demand, clamp_capacity, menu_price_median
from foodops.ui.director_office import bureau_directeur
from ..core.game_types import TurnResult
from ..ui.results_view import print_turn_result
from ..core.accounting import (
    month_amortization, post_sales, post_cogs, post_services_ext,
    post_payroll, post_depreciation, post_loan_payment
)
from ..ui.accounting_view import print_income_statement, print_balance_sheet


@dataclass
class Game:
    restaurants: List[Restaurant]
    scenario: DefaultScenario = field(default_factory=DefaultScenario)
    current_tour: int = 1

    def play(self) -> None:
        nb_tours = self.scenario.nb_tours

        # --- Bureau du directeur juste après bilan initial ---
        for r in self.restaurants:
            if hasattr(r, "equipe") and hasattr(r, "type_resto"):
                print(f"\nOuverture du Bureau du Directeur pour {r.name}")
                r.equipe = bureau_directeur(r.equipe, r.type_resto)

        # --- Boucle de jeu ---
        while self.current_tour <= nb_tours:
            print(f"\n=== 📅 Tour {self.current_tour}/{nb_tours} ===")
            demand = self.scenario.demand_per_tour
            attrib = allocate_demand(self.restaurants, demand)
            served = clamp_capacity(self.restaurants, attrib)

            for i, r in enumerate(self.restaurants):
                price_med = menu_price_median(r)

                # Création d'un TurnResult complet
                tr = TurnResult.from_game_state(
                    r=r,
                    clients_attr=attrib.get(i, 0),
                    clients_serv=served.get(i, 0),
                    price_med=price_med
                )

                # --- Affichage résultats gameplay ---
                print_turn_result(tr)

                # --- COMPTABILISATION ---
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
                    i = round(outstanding * (annual_rate / 12.0), 2)
                    p = max(0.0, round(monthly_payment - i, 2))
                    new_out = max(0.0, round(outstanding - p, 2))
                    return (i, p, new_out)

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

                # Mise à jour de la trésorerie gameplay
                r.funds = tr.funds_end - (i_bpi + p_bpi + i_bank + p_bank)

                # --- AFFICHAGE COMPTA ---
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

def print_turn_result(tr):
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    print(f"\n{CYAN}📊 --- Résultats du tour ---{RESET}")
    print(f"🏪 Restaurant : {tr.restaurant_name}")
    print(f"🗓️  Tour       : {tr.tour}")
    print(f"👥 Clients attribués : {tr.clients_attr}")
    print(f"✅ Clients servis    : {tr.clients_serv} "
          f"({(tr.clients_serv / tr.clients_attr * 100) if tr.clients_attr else 0:.1f} % servis)")
    print(f"📈 Capacité utilisée : {(tr.clients_serv / tr.capacity * 100) if tr.capacity else 0:.1f} %")
    print(f"💶 Prix médian menu  : {tr.price_med:.2f} €")
    print(f"💰 Chiffre d'affaires: {tr.ca:.2f} €")

    print(f"\n{YELLOW}💸 --- Dépenses principales ---{RESET}")
    print(f"🥗 Achats consommés (matières) : {tr.cogs:.2f} €")
    print(f"🧑‍🍳 Charges de personnel        : {tr.rh_cost:.2f} € "
          f"(~{(tr.rh_cost / tr.clients_serv) if tr.clients_serv else 0:.2f} €/client)")
    print(f"📢 Marketing                   : {tr.marketing:.2f} €")
    print(f"🏢 Services extérieurs          : {tr.fixed_costs:.2f} €")

    print(f"\n{CYAN}📈 --- Résultat du tour ---{RESET}")
    resultat_tour = tr.ca - tr.cogs - tr.rh_cost - tr.fixed_costs - tr.marketing
    couleur_result = GREEN if resultat_tour >= 0 else RED
    emoji_result = "🟢" if resultat_tour >= 0 else "🔴"
    print(f"{emoji_result} Résultat avant amort./intérêts : {couleur_result}{resultat_tour:.2f} €{RESET}")

    print(f"\n{CYAN}💼 --- Trésorerie ---{RESET}")
    couleur_fonds = GREEN if tr.funds_end >= tr.funds_start else RED
    print(f"💳 Début tour : {tr.funds_start:.2f} €")
    print(f"💳 Fin tour   : {couleur_fonds}{tr.funds_end:.2f} €{RESET}")
