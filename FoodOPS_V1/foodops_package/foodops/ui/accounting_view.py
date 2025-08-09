# foodops/ui/accounting_view.py

def _posneg(val):
    """Affiche les valeurs positives sans signe, et les négatives avec un signe négatif."""
    return f"{val:,.2f} €" if val >= 0 else f"-{abs(val):,.2f} €"


def print_income_statement(cr):
    print("\n📊 Compte de Résultat (par tour)")
    print("=" * 40)
    print(f"  💶 Chiffre d'affaires (70) : {_posneg(cr['Chiffre d\'affaires (70)'])}")
    print(f"  🛒 Achats consommés (60) : {_posneg(cr['Achats consommés (60)'])}")
    print(f"  🛠 Services extérieurs (61/62) : {_posneg(cr['Services extérieurs (61/62)'])}")
    print(f"  👥 Charges de personnel (64) : {_posneg(cr['Charges de personnel (64)'])}")
    print(f"  📉 Dotations amortissements (68) : {_posneg(cr['Dotations amortissements (68)'])}")
    print("-" * 40)
    print(f"  📈 Résultat d'exploitation : {_posneg(cr['Résultat d\'exploitation'])}")
    print("=" * 40)


def print_balance_sheet(bs):
    print("\n📒 Bilan")
    print("=" * 40)
    print("Actif :")
    print(f"  💰 Trésorerie : {_posneg(bs['Trésorerie'])}")
    print(f"  📦 Stock : {_posneg(bs['Stock'])}")
    print(f"  🏢 Immobilisations nettes : {_posneg(bs['Immobilisations nettes'])}")
    print("-" * 40)
    print("Passif :")
    print(f"  🏦 Emprunts BPI : {_posneg(bs['Emprunts BPI'])}")
    print(f"  🏦 Emprunts bancaires : {_posneg(bs['Emprunts bancaires'])}")
    print(f"  📊 Capitaux propres : {_posneg(bs['Capitaux propres'])}")
    print("=" * 40)
    print(f"  💰 Trésorerie début : {_posneg(bs['Trésorerie début'])}")
    print(f"  💰 Trésorerie fin : {_posneg(bs['Trésorerie fin'])}")