from FoodOPS_V1.domain.restaurant import Restaurant
from FoodOPS_V1.core.accounting import balance_sheet


def format_to_euro(x: float) -> str:
    """Format a float as a euro currency string (no decimals, thin spaces)."""
    return f"{x:,.0f} €".replace(",", " ").replace(".0", "")


def _posneg(val):
    """Affiche les valeurs positives sans signe, et les négatives avec un signe négatif."""
    return f"{val:,.2f} €".replace(",", " ")


def print_income_statement(cr, title: str):
    print(title)
    print("=" * 40)
    print(f"  💶 Chiffre d'affaires (70) : {_posneg(cr["Chiffre d'affaires (70)"])}")
    print(f"  🛒 Achats consommés (60) : {_posneg(cr['Achats consommés (60)'])}")
    print(
        f"  🛠 Services extérieurs (61/62) : {_posneg(cr['Services extérieurs (61/62)'])}"
    )
    print(
        f"  👥 Charges de personnel (64) : {_posneg(cr['Charges de personnel (64)'])}"
    )
    print(
        f"  📉 Dotations amortissements (68) : {_posneg(cr['Dotations amortissements (68)'])}"
    )
    print("-" * 40)
    print(f"  📈 Résultat d'exploitation : {_posneg(cr["Résultat d'exploitation"])}")
    print("=" * 40)


def print_balance_sheet(balance_sheet):
    print("\n📒 Bilan")
    print("=" * 40)
    print("Actif :")
    print(f"  💰 Trésorerie : {_posneg(balance_sheet['Trésorerie'])}")
    print(f"  📦 Stock : {_posneg(balance_sheet['Stock'])}")
    print(
        f"  🏢 Immobilisations nettes : {_posneg(balance_sheet['Immobilisations nettes'])}"
    )
    print("-" * 40)
    print("Passif :")
    print(f"  🏦 Emprunts BPI : {_posneg(balance_sheet['Emprunts BPI'])}")
    print(f"  🏦 Emprunts bancaires : {_posneg(balance_sheet['Emprunts bancaires'])}")
    print(f"  📊 Capitaux propres : {_posneg(balance_sheet['Capitaux propres'])}")
    print("=" * 40)
    print(f"  💰 Trésorerie début : {_posneg(balance_sheet['Trésorerie début'])}")
    print(f"  💰 Trésorerie fin : {_posneg(balance_sheet['Trésorerie fin'])}")


def print_opening_balance(restaurant: Restaurant):
    """Print a simple human-readable opening balance for a restaurant.

    Shows the main balance sheet lines at tour 0 to help players understand
    their starting financial position.
    """
    # Solde des comptes à l'ouverture (tour 0)
    bal = restaurant.ledger.balance_accounts(upto_tour=0)
    bs = balance_sheet(bal)
    actif = bs.actif
    passif = bs.passif

    print("\n🧾  Bilan d'ouverture —", restaurant.name)
    print("═" * 52)
    print("ACTIF")
    print(f"🏭 Immobilisations (215): {format_to_euro(actif.immobilisations_brutes)}")
    print(f"(-) Amort. cumulés (2815): {format_to_euro(actif.amortissements_cumules)}")
    print(f"= Immobilisations nettes: {format_to_euro(actif.immobilisations_nettes)}")
    print(f"💶 Trésorerie (512): {format_to_euro(actif.trésorerie)}")
    print(f"👉 TOTAL ACTIF: {format_to_euro(actif.total)}")

    print("\nPASSIF")
    print(f"🧱 Capitaux propres (101): {format_to_euro(passif.capitaux_propres)}")
    print(f"🏦 Emprunts (164): {format_to_euro(passif.emprunts)}")
    print(f"👉 TOTAL PASSIF : {format_to_euro(passif.total)}")
    print("═" * 52)


def print_resume_financement(restaurant: Restaurant, financing_plan):
    local = restaurant.local
    equip_default = restaurant.equipment_invest
    plan = financing_plan

    print(f"\n💼 {restaurant.name} — {restaurant.type.value}")
    print(
        f"📍Local: {local.nom} | Capacité: {local.capacite_clients}couverts/jour | Loyer: {format_to_euro(local.loyer)}/mois"
    )
    print(f"🧰Équipementinitial: {format_to_euro(equip_default)}")
    print(
        f"🏦Banque: {format_to_euro(plan.bank_loan)}→Mensualité~{format_to_euro(plan.bank_monthly)}"
    )
    print(
        f"🏛️BPI: {format_to_euro(plan.bpi_loan)}→Mensualité~{format_to_euro(plan.bpi_monthly)}"
    )
    print(f"🧾Fraisdedossier(3%): {format_to_euro(plan.frais_dossier)}")
    print(f"💶Trésoreriededépart: {format_to_euro(plan.cash_initial)}")
