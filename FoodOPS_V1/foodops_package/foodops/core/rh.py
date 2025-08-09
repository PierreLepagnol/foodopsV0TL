# -*- coding: utf-8 -*-
"""
Moteur RH : calcul coûts, capacités, satisfaction, et gestion contrats.
"""

from ..data.roles import ROLES

CHARGES_PATRONALES = 0.42  # 42% charges patronales
COUT_LICENCIEMENT_MOIS = 1  # 1 mois de salaire brut
COUT_EMBAUCHE_FIXE = 400    # coût comptable / administratif

def calcul_cout_mensuel(equipe):
    """
    Calcule le coût mensuel total (salaires + charges).
    """
    total = 0
    for employe in equipe:
        total += employe["salaire"] * (1 + CHARGES_PATRONALES)
    return total

def calcul_capacite_totale(equipe, type_resto):
    """
    Additionne les capacités couverts/tour selon les rôles.
    """
    base_roles = {r["nom"]: r for r in ROLES[type_resto]}
    capacite = 0
    for employe in equipe:
        role = base_roles.get(employe["nom"])
        if role:
            capacite += role["capacite_couverts"]
    return capacite

def calcul_satisfaction(equipe, type_resto, clients_servis):
    """
    Calcule la satisfaction moyenne.
    Basé sur : salaire vs marché, charge de travail.
    """
    if not equipe:
        return 0

    base_roles = {r["nom"]: r for r in ROLES[type_resto]}
    capacite = calcul_capacite_totale(equipe, type_resto)
    if capacite == 0:
        return 0

    satisfaction_total = 0
    for employe in equipe:
        role = base_roles.get(employe["nom"])
        if not role:
            continue

        # Salaire vs marché
        ratio_salaire = employe["salaire"] / role["salaire_marche"]
        satisfaction = 70
        if ratio_salaire < 1.0:
            satisfaction -= (1.0 - ratio_salaire) * 30
        elif ratio_salaire > 1.1:
            satisfaction += (ratio_salaire - 1.1) * 20

        # Charge de travail
        charge_ratio = clients_servis / capacite
        if charge_ratio > 1.0:
            satisfaction -= (charge_ratio - 1.0) * 50
        elif charge_ratio < 0.7:
            satisfaction -= (0.7 - charge_ratio) * 10

        satisfaction_total += max(0, min(100, satisfaction))

    return satisfaction_total / len(equipe)

def cout_licenciement(employe):
    """
    Calcule le coût de licenciement d'un employé.
    """
    return employe["salaire"] * COUT_LICENCIEMENT_MOIS

def cout_embauche(salaire):
    """
    Calcule le coût d'embauche (fixe + salaire premier mois).
    """
    return COUT_EMBAUCHE_FIXE + salaire * (1 + CHARGES_PATRONALES)
