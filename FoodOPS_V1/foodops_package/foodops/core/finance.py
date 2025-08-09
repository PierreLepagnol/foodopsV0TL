from dataclasses import dataclass

@dataclass
class FinancingPlan:
    apport: float
    bank_loan: float
    bpi_loan: float
    frais_dossier: float
    bank_monthly: float
    bpi_monthly: float
    bank_outstanding: float
    bpi_outstanding: float
    cash_initial: float

# constantes gameplay
APPORT_FIXE = 50_000.0
BANQUE_FIXE = 250_000.0
BPI_MAX = 20_000.0
FRAIS_PCT = 0.03
TAUX_BANQUE = 0.045  # annuel
TAUX_BPI = 0.025     # annuel
DUREE_BANQUE = 60    # mois
DUREE_BPI = 48       # mois

def propose_financing(fonds_price: float, equip_default: float) -> FinancingPlan:
    """
    Calcule un plan de financement réaliste selon les règles admin fixes.
    """
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
        cash_initial=cash_initial
    )
