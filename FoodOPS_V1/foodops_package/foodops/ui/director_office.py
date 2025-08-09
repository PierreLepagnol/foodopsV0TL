# foodops/ui/director_office.py
# -*- coding: utf-8 -*-
from typing import List, Dict
import random

def _eur(x: float) -> str:
    return f"{x:,.0f} €".replace(",", " ").replace(".0", "")

def _prompt_float(prompt: str, default: float = 0.0) -> float:
    try:
        s = input(prompt).strip().replace(",", ".")
        return float(s)
    except Exception:
        return default

def _prompt_int(prompt: str, default: int = 0) -> int:
    try:
        return int(input(prompt).strip())
    except Exception:
        return default

def _ensure_hr_fields(r):
    if not hasattr(r, "equipe"):
        r.equipe = []
    if not hasattr(r, "hr_salary_delta"):
        r.hr_salary_delta = 0.0   # % global vs marché
    if not hasattr(r, "marketing_budget"):
        r.marketing_budget = 0.0
    if not hasattr(r, "pricing_markup"):
        r.pricing_markup = 0.0    # % appliqué sur les prix conseillés
    if not hasattr(r, "quality_index"):
        r.quality_index = 0.6
    if not hasattr(r, "service_index"):
        r.service_index = 0.6

def _hr_cost_month(r) -> float:
    # Somme brute simplifiée
    total = 0.0
    for emp in r.equipe:
        total += getattr(emp, "salaire_mensuel", 0.0)
    # Ajustement global
    total *= (1.0 + getattr(r, "hr_salary_delta", 0.0))
    return round(total, 2)

def _show_team(r):
    print("\n--- Équipe actuelle ---")
    if not r.equipe:
        print("(vide)")
    else:
        for i, emp in enumerate(r.equipe, 1):
            sal = getattr(emp, "salaire_mensuel", 0.0)
            print(f"{i}. {emp.nom} {emp.prenom} - {emp.poste} - {_eur(sal)}")
    print("-" * 23)
    print(f"Coût mensuel: {_eur(_hr_cost_month(r))}")

# ——— Actions ———

def _action_recruter(r):
    # Faux vivier minimaliste
    pool = [
        {"nom":"Alex","prenom":"Roux","poste":"Équipier polyvalent","salaire_mensuel":1550},
        {"nom":"Marie","prenom":"Lefevre","poste":"Serveur","salaire_mensuel":1650},
        {"nom":"Karim","prenom":"Garcia","poste":"Manager","salaire_mensuel":2500},
        {"nom":"Sophie","prenom":"Bernard","poste":"Plongeur","salaire_mensuel":1500},
        {"nom":"Lucas","prenom":"Petit","poste":"Cuisinier","salaire_mensuel":1900},
    ]
    for i, c in enumerate(pool, 1):
        print(f"{i}. {c['nom']} {c['prenom']} - {c['poste']} - {_eur(c['salaire_mensuel'])}/mois")
    idx = _prompt_int("Sélectionnez un candidat: ", 0)
    if 1 <= idx <= len(pool):
        c = pool[idx-1]
        prop = _prompt_float("Salaire proposé: ", c["salaire_mensuel"])
        # règle simple d’acceptation
        seuil = c["salaire_mensuel"] * 0.97
        if prop >= seuil:
            # on enregistre l’employé
            emp = type("Emp", (), {})()
            emp.nom = c["nom"]; emp.prenom = c["prenom"]
            emp.poste = c["poste"]; emp.salaire_mensuel = prop
            r.equipe.append(emp)
            print("Embauche réussie!")
        else:
            print("Refusé.")
    else:
        print("Annulé.")

def _action_licencier(r):
    if not r.equipe:
        print("Aucun salarié.")
        return
    _show_team(r)
    idx = _prompt_int("Qui licencier ? (numéro) ", 0)
    if 1 <= idx <= len(r.equipe):
        emp = r.equipe.pop(idx-1)
        # coût de licenciement simplifié
        cout = getattr(emp, "salaire_mensuel", 0.0) * 0.5
        r.funds -= cout
        print(f"{emp.nom} {emp.prenom} licencié. Coût: {_eur(cout)}")
    else:
        print("Annulé.")

def _action_ajuster_salaires(r):
    delta = _prompt_float("Ajustement global salaires en % (ex: 5 ou -5): ", 0.0) / 100.0
    r.hr_salary_delta = max(-0.1, min(0.1, delta))  # borne +/-10%
    print(f"Delta salaires appliqué: {r.hr_salary_delta*100:.1f}%")

def _action_marketing(r):
    budget = _prompt_float("Budget marketing mensuel (€): ", getattr(r, "marketing_budget", 0.0))
    budget = max(0.0, budget)
    r.marketing_budget = budget
    # On met ça dans overheads['autres'] pour que ça impacte le compte de résultat
    r.overheads["autres"] = r.overheads.get("autres", 0.0) + budget
    # Petit boost de notoriété plafonné
    r.notoriety = min(1.0, getattr(r, "notoriety", r.notoriety) + min(0.05, budget / 20000.0))
    print(f"Marketing mensuel: {_eur(budget)} — Notoriété: {r.notoriety:.2f}")

def _action_prix_menu(r):
    mk = _prompt_float("Markup prix menu en % (ex: 0, 10, 25): ", getattr(r, "pricing_markup", 0.0)*100) / 100.0
    r.pricing_markup = max(0.0, min(1.0, mk))  # 0% à 100%
    print(f"Markup menu réglé à {r.pricing_markup*100:.0f}%")

def _action_maintenance_qualite(r):
    spend = _prompt_float("Budget maintenance/qualité ce tour (€): ", 0.0)
    if spend > 0:
        r.funds -= spend
        r.quality_index = min(1.0, getattr(r, "quality_index", 0.6) + min(0.08, spend / 25000.0))
        print(f"Qualité: {r.quality_index:.2f} — Trésorerie: {_eur(r.funds)}")
    else:
        print("Aucun changement.")

def _action_formation_service(r):
    spend = _prompt_float("Budget formation service ce tour (€): ", 0.0)
    if spend > 0:
        r.funds -= spend
        r.service_index = min(1.0, getattr(r, "service_index", 0.6) + min(0.08, spend / 25000.0))
        print(f"Service: {r.service_index:.2f} — Trésorerie: {_eur(r.funds)}")
    else:
        print("Aucun changement.")

def _action_recap_rh(r):
    _show_team(r)

# ——— Entrée principale ———

def bureau_directeur(equipe_init: List = None, type_resto: str = "") -> List:
    # r est injecté par game.py : on manipule l’objet directement
    # Ici, on retourne seulement l’équipe (back-compat de l’appel existant).
    current_restaurant = getattr(bureau_directeur, "_r", None)
    if current_restaurant is None:
        # fallback si jamais on a besoin
        class Dummy:
            equipe = equipe_init or []
            funds = 0.0
            notoriety = 0.5
            overheads = {"autres": 0.0}
            local = type("L", (), {"visibilite":1.0})()
        bureau_directeur._r = Dummy()
    r = bureau_directeur._r
    _ensure_hr_fields(r)

    while True:
        print("\n=== Bureau du Directeur ===")
        print("1. Voir équipe")
        print("2. Recruter")
        print("3. Licencier")
        print("4. Ajuster salaires (global)")
        print("5. Budget marketing")
        print("6. Politique de prix (markup)")
        print("7. Maintenance / Qualité")
        print("8. Formation service")
        print("9. Récap RH")
        print("0. Quitter bureau")
        choice = input("> ").strip()

        if choice == "1":
            _show_team(r)
        elif choice == "2":
            _action_recruter(r)
        elif choice == "3":
            _action_licencier(r)
        elif choice == "4":
            _action_ajuster_salaires(r)
        elif choice == "5":
            _action_marketing(r)
        elif choice == "6":
            _action_prix_menu(r)
        elif choice == "7":
            _action_maintenance_qualite(r)
        elif choice == "8":
            _action_formation_service(r)
        elif choice == "9":
            _action_recap_rh(r)
        elif choice == "0":
            break
        else:
            print("Choix invalide.")

    return r.equipe
