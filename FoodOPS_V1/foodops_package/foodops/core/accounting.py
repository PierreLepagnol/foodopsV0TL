# -*- coding: utf-8 -*-
"""
Journal, comptes, compte de résultat et bilan (format FR simplifié).
Sans TVA pour l'instant, focus pédagogie.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from ..data.accounting_params import ACCOUNTS, EQUIP_AMORT_YEARS

@dataclass
class Entry:
    tour: int
    lines: List[Tuple[str, float, str]]  # (compte, montant, 'D'|'C')
    label: str = ""

@dataclass
class Ledger:
    """Grand livre minimaliste."""
    entries: List[Entry] = field(default_factory=list)

    def post(self, tour: int, label: str, lines: List[Tuple[str, float, str]]):
        # contrôle équilibre
        d = sum(m for c, m, dc in lines if dc == 'D')
        c = sum(m for c, m, dc in lines if dc == 'C')
        if round(d - c, 2) != 0.0:
            raise ValueError(f"Écriture non équilibrée '{label}': {d} != {c}")
        self.entries.append(Entry(tour=tour, lines=lines, label=label))

    def balance_accounts(self, upto_tour: int = None) -> Dict[str, float]:
        """Solde des comptes (Débit - Crédit)."""
        bal: Dict[str, float] = {}
        for e in self.entries:
            if upto_tour is not None and e.tour > upto_tour:
                continue
            for acc, amt, dc in e.lines:
                bal.setdefault(acc, 0.0)
                bal[acc] += amt if dc == 'D' else -amt
        return bal

def month_amortization(amount: float) -> float:
    """Dotation mensuelle linéaire de l'équipement (1 tour = 1 mois)."""
    months = EQUIP_AMORT_YEARS * 12
    return 0.0 if amount <= 0 else round(amount / months, 2)

# ------- Générateurs d'écritures types (par tour) -------

def post_opening(ledger: Ledger, equity: float, cash: float, equipment: float, loans_total: float):
    """Écriture d'ouverture simple équilibrée."""
    lines: List[Tuple[str, float, str]] = []
    if cash > 0:
        lines.append(("512", cash, "D"))
    if equipment > 0:
        lines.append(("215", equipment, "D"))
    if loans_total > 0:
        lines.append(("164", loans_total, "C"))
    # Capitaux propres = équilibre
    # Total D - Total C = capitaux propres (C si D>C)
    total_d = sum(m for a, m, dc in lines if dc == "D")
    total_c = sum(m for a, m, dc in lines if dc == "C")
    # Si equity donné, on force l'équilibre avec 101 au passif
    if equity is not None:
        lines.append(("101", equity, "C"))
    else:
        diff = total_d - total_c
        if diff > 0:
            lines.append(("101", diff, "C"))
        elif diff < 0:
            lines.append(("101", -diff, "D"))
    ledger.post(0, "Ouverture", lines)

def post_sales(ledger: Ledger, tour: int, ca: float):
    if ca <= 0: return
    ledger.post(tour, "Ventes", [
        ("512", ca, "D"),
        ("70",  ca, "C"),
    ])

def post_cogs(ledger: Ledger, tour: int, cogs: float):
    if cogs <= 0: return
    ledger.post(tour, "Achats consommés (matières)", [
        ("60",  cogs, "D"),
        ("512", cogs, "C"),
    ])

def post_services_ext(ledger: Ledger, tour: int, amount: float):
    if amount <= 0: return
    ledger.post(tour, "Services extérieurs (loyer, abonnements, marketing)", [
        ("61",  amount, "D"),
        ("512", amount, "C"),
    ])

def post_payroll(ledger: Ledger, tour: int, payroll_total: float):
    if payroll_total <= 0: return
    ledger.post(tour, "Charges de personnel", [
        ("64",  payroll_total, "D"),
        ("512", payroll_total, "C"),
    ])

def post_depreciation(ledger: Ledger, tour: int, dotation: float):
    if dotation <= 0: return
    ledger.post(tour, "Dotations aux amortissements", [
        ("681",  dotation, "D"),
        ("2815", dotation, "C"),
    ])

def post_loan_payment(ledger: Ledger, tour: int, interest: float, principal: float, label: str):
    if interest <= 0 and principal <= 0: return
    lines: List[Tuple[str, float, str]] = []
    if interest > 0:
        lines += [("66", interest, "D"), ("512", interest, "C")]
    if principal > 0:
        lines += [("164", principal, "D"), ("512", principal, "C")]
    ledger.post(tour, f"Remboursement {label}", lines)

# ------- États (compte de résultat / bilan) -------

def income_statement(bal: Dict[str, float]) -> Dict[str, float]:
    """Compte de résultat (soldes débit-crédit agrégés)."""
    ventes = -(bal.get("70", 0.0))             # 70 est créditor
    cogs = bal.get("60", 0.0)
    services = bal.get("61", 0.0)
    payroll = bal.get("64", 0.0)
    depreciation = bal.get("681", 0.0)
    financial = bal.get("66", 0.0)

    marge_brute = ventes - cogs
    ebe_like = ventes - cogs - services - payroll
    rex = ebe_like - depreciation
    rca = rex - financial
    res_net = rca  # pas d'IS ni exceptionnel dans cette V1

    return {
        "Chiffre d'affaires (70)": ventes,
        "Achats consommés (60)": cogs,
        "Services extérieurs (61)": services,
        "Charges de personnel (64)": payroll,
        "Dotations amort. (681)": depreciation,
        "Charges financières (66)": financial,
        "Marge brute": marge_brute,
        "EBE (approx)": ebe_like,
        "Résultat d'exploitation": rex,
        "Résultat courant": rca,
        "Résultat net": res_net,
    }

def balance_sheet(bal: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """Bilan (actif/passif) à partir des soldes."""
    actif_brut = {
        "Immobilisations (215)": bal.get("215", 0.0),
        "Amortissements cumulés (2815)": -bal.get("2815", 0.0),
        "Trésorerie (512)": bal.get("512", 0.0),
    }
    immobilisations_nettes = actif_brut["Immobilisations (215)"] + actif_brut["Amortissements cumulés (2815)"]
    actif_total = immobilisations_nettes + actif_brut["Trésorerie (512)"]

    passif = {
        "Capitaux propres (101)": -bal.get("101", 0.0),
        "Emprunts (164)": -bal.get("164", 0.0),
    }
    passif_total = passif["Capitaux propres (101)"] + passif["Emprunts (164)"]

    return {
        "Actif": {
            **actif_brut,
            "Immobilisations nettes": immobilisations_nettes,
            "Total Actif": actif_total,
        },
        "Passif": {
            **passif,
            "Total Passif": passif_total,
        }
    }
