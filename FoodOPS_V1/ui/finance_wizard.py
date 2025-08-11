from FoodOPS_V1.core.finance import propose_financing


def run_finance_wizard(local_price: float, equip_cost: float):
    """Synthèse du financement (apport admin + banque fixe + BPI max)."""
    invest_total_no_fees = local_price + equip_cost
    plan = propose_financing(invest_total_no_fees)

    print("\n=== RÈGLES DE FINANCEMENT (fixées par l'admin) ===")
    print("• Apport de départ (obligatoire) : 50 000 €")
    print("• Prêt bancaire fixe            : 250 000 €")
    print(
        "• Prêt BPI (max)                : 20 000 € (accordé d'office, ajusté selon besoin)"
    )
    print("• Frais d'installation          : 3 % de l'investissement\n")

    print("=== PLAN DE FINANCEMENT ===")
    print(f"Investissement (fonds + équipement) : {invest_total_no_fees:.0f} €")
    print(
        f"Frais d'installation inclus         : {plan['invest_total_with_fees']:.0f} €"
    )
    print(f"Apport (admin)                      : {plan['apport']:.0f} €")
    print(
        f"Crédit Banque (fixe)                : {plan['bank_amount']:.0f} € -> {plan['bank_monthly']:.0f} €/mois"
    )
    print(
        f"Crédit BPI (<=20k)                  : {plan['bpi_amount']:.0f} € -> {plan['bpi_monthly']:.0f} €/mois"
    )
    print(f"Total financements                  : {plan['total_funding']:.0f} €")
    print(f"Trésorerie de départ                : {plan['cash_start']:.0f} €")
    print("Charges fixes hors prêt (€/mois)    :")
    for k, v in plan["fixed_overheads"].items():
        print(f"  - {k}: {v:.0f} €")

    input("\n[Entrée] pour valider ce plan...")
    return plan
