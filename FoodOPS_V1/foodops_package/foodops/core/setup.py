# -*- coding: utf-8 -*-
from ..domain import Restaurant, RestaurantType
from ..data.locals_presets import DEFAULT_LOCALS
from ..data.menus_presets_simple import get_default_menus_simple
from .finance import propose_financing
from .accounting import Ledger, post_opening, balance_sheet

def _fmt_eur(x: float) -> str:
    return f"{x:,.0f} €".replace(",", " ").replace(".0", "")

def _print_opening_balance(restaurant: Restaurant):
    # Solde des comptes à l'ouverture (tour 0)
    bal = restaurant.ledger.balance_accounts(upto_tour=0)
    bs = balance_sheet(bal)

    a = bs["Actif"]
    p = bs["Passif"]

    print("\n🧾  Bilan d’ouverture —", restaurant.name)
    print("═" * 52)
    print("ACTIF")
    print(f"  🏭 Immobilisations (215)        : {_fmt_eur(a['Immobilisations (215)'])}")
    print(f"  (–) Amort. cumulés (2815)      : {_fmt_eur(a['Amortissements cumulés (2815)'])}")
    print(f"  =  Immobilisations nettes      : {_fmt_eur(a['Immobilisations nettes'])}")
    print(f"  💶 Trésorerie (512)             : {_fmt_eur(a['Trésorerie (512)'])}")
    print(f"  👉 TOTAL ACTIF                  : {_fmt_eur(a['Total Actif'])}")

    print("\nPASSIF")
    print(f"  🧱 Capitaux propres (101)       : {_fmt_eur(p['Capitaux propres (101)'])}")
    print(f"  🏦 Emprunts (164)               : {_fmt_eur(p['Emprunts (164)'])}")
    print(f"  👉 TOTAL PASSIF                 : {_fmt_eur(p['Total Passif'])}")
    print("═" * 52)

def create_restaurants():
    restaurants = []

    menus_by_type = get_default_menus_simple()

    # Saisie du nombre de joueurs ici (la CLI n’envoie plus le param)
    while True:
        try:
            nb_joueurs = int(input("Nombre de joueurs (1–8) : ").strip())
            if 1 <= nb_joueurs <= 8:
                break
        except Exception:
            pass
        print("  ⚠️  Saisis un entier entre 1 et 8.")

    for i in range(nb_joueurs):
        print(f"\n— Joueur {i+1} —")
        print("Types : 1) Fast Food  2) Bistrot  3) Gastronomique")
        while True:
            try:
                t = int(input("Type de restaurant : ").strip())
                if t in (1, 2, 3):
                    break
            except Exception:
                pass
            print("  ⚠️  Choisis 1, 2 ou 3.")

        type_keys = {1: "FAST_FOOD", 2: "BISTRO", 3: "GASTRO"}
        type_resto = type_keys[t]

        # Sélection du local (simple: premier de la liste pour ce type)
        local = DEFAULT_LOCALS[type_resto][0]

        # Équipement par défaut selon type (tu pourras affiner)
        equip_default = 80_000.0 if type_resto == "FAST_FOOD" else (120_000.0 if type_resto == "BISTRO" else 180_000.0)

        # Plan de financement selon règles admin
        plan = propose_financing(local.prix_fond, equip_default)

        # Création du restaurant
        r = Restaurant(
            name=f"Resto {i+1}",
            type=RestaurantType[type_resto],
            local=local,
            funds=plan.cash_initial,               # trésorerie après financement - investissement - frais
            equipment_invest=equip_default,
            menu=menus_by_type[RestaurantType[type_resto]],
            notoriety=0.5,
            overheads={"loyer": local.loyer, "autres": 0.0},
            monthly_bpi=plan.bpi_monthly,
            monthly_bank=plan.bank_monthly,
            bpi_outstanding=plan.bpi_outstanding,
            bank_outstanding=plan.bank_outstanding,
        )

        # Initialiser la compta + écriture d'ouverture
        r.ledger = Ledger()
        total_loans = plan.bank_loan + plan.bpi_loan
        post_opening(
            r.ledger,
            equity=None,                   # auto-équilibrage 101
            cash=r.funds,                  # tréso initiale
            equipment=r.equipment_invest,  # immobilisations
            loans_total=total_loans        # dette initiale
        )

        # Résumé financement et bilan d’ouverture
        print(f"\n💼  {r.name} — {r.type.value}")
        print(f"📍 Local: {local.nom}  |  Capacité: {local.capacite_clients} couverts/jour  |  Loyer: {_fmt_eur(local.loyer)}/mois")
        print(f"🧰 Équipement initial : {_fmt_eur(equip_default)}")
        print(f"🏦 Banque : {_fmt_eur(plan.bank_loan)}  → Mensualité ~ {_fmt_eur(plan.bank_monthly)}")
        print(f"🏛️ BPI   : {_fmt_eur(plan.bpi_loan)}   → Mensualité ~ {_fmt_eur(plan.bpi_monthly)}")
        print(f"🧾 Frais de dossier (3%) : {_fmt_eur(plan.frais_dossier)}")
        print(f"💶 Trésorerie de départ  : {_fmt_eur(plan.cash_initial)}")

        _print_opening_balance(r)

        restaurants.append(r)

    return restaurants
