# -*- coding: utf-8 -*-
# foodops/ui/results_view.py

from typing import Optional


# ---------- Helpers de formatage ----------

def _fmt_eur(x: float) -> str:
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return f"{x} €"

def _pct(a: float, b: float) -> str:
    try:
        if b <= 0:
            return "—"
        v = max(0.0, min(1.0, float(a) / float(b))) * 100.0
        return f"{v:5.1f}%"
    except Exception:
        return "—"

def _bar(current: int, maxv: int, width: int = 24, fill_char: str = "█") -> str:
    if maxv <= 0:
        return " " * width
    ratio = max(0.0, min(1.0, float(current) / float(maxv)))
    n = int(round(ratio * width))
    return fill_char * n + " " * (width - n)

def _num(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0


# ---------- Impression d’un tour ----------

def print_turn_result(tr) -> None:
    """
    Attend un objet 'tr' (SimpleNamespace ou dataclass) avec au minimum :
      restaurant_name: str
      tour: int
      clients_attr: int
      clients_serv: int
      capacity: int
      price_med: float
      ca: float
      cogs: float
      fixed_costs: float
      marketing: float
      rh_cost: float
      funds_start: float
      funds_end: float
    """

    name = getattr(tr, "restaurant_name", "Restaurant")
    tour = getattr(tr, "tour", 0)

    # Demande & capacité
    clients_attr = _num(getattr(tr, "clients_attr", 0))
    clients_serv = _num(getattr(tr, "clients_serv", 0))
    capacity     = _num(getattr(tr, "capacity", 0))

    # Prix & ventes
    price_med = float(getattr(tr, "price_med", 0.0) or 0.0)
    ca        = float(getattr(tr, "ca", 0.0) or 0.0)
    cogs      = float(getattr(tr, "cogs", 0.0) or 0.0)

    # OPEX
    fixed_costs = float(getattr(tr, "fixed_costs", 0.0) or 0.0)
    marketing   = float(getattr(tr, "marketing", 0.0) or 0.0)
    rh_cost     = float(getattr(tr, "rh_cost", 0.0) or 0.0)

    funds_start = float(getattr(tr, "funds_start", 0.0) or 0.0)
    funds_end   = float(getattr(tr, "funds_end", 0.0) or 0.0)

    # KPIs dérivés
    asp = ca / clients_serv if clients_serv > 0 else price_med
    gross_margin = ca - cogs
    opex = fixed_costs + marketing + rh_cost
    operating_result = gross_margin - opex

    # Barres
    cap_bar = _bar(clients_serv, max(1, capacity))
    dem_bar = _bar(clients_serv, max(1, clients_attr))

    print(f"\n────────────────────────────────────────────────────────────────────────────")
    print(f"  📊 Résultat — {name} — Tour {tour}")
    print(f"────────────────────────────────────────────────────────────────────────────")

    # Ligne demande/capacité
    print(f"  Demande attribuée : {clients_attr:>6d}   Couvert(s) servi(s) : {clients_serv:>6d}")
    print(f"  Capacité RH/salle : {capacity:>6d}   Utilisation capacité : {_pct(clients_serv, capacity):>6}")
    print(f"  Couverture demande: {_pct(clients_serv, clients_attr):>6}")
    print(f"  [{cap_bar}] Capacité")
    print(f"  [{dem_bar}] Demande  ")

    # Prix & CA
    print(f"\n  Prix médian menu : {_fmt_eur(price_med):>12}   Ticket moyen (réel) : {_fmt_eur(asp):>12}")
    print(f"  Chiffre d’affaires: {_fmt_eur(ca):>12}")

    # COGS & marge
    print(f"  COGS (coût prod)  : {_fmt_eur(cogs):>12}")
    print(f"  Marge brute       : {_fmt_eur(gross_margin):>12}   (taux: {_pct(gross_margin, ca)})")

    # OPEX
    print(f"\n  Coûts fixes       : {_fmt_eur(fixed_costs):>12}")
    print(f"  Marketing         : {_fmt_eur(marketing):>12}")
    print(f"  Masse salariale   : {_fmt_eur(rh_cost):>12}")
    print(f"  OPEX total        : {_fmt_eur(opex):>12}")

    # Résultat opé
    print(f"\n  Résultat opé.     : {_fmt_eur(operating_result):>12}")

    # Tréso
    print(f"\n  Trésorerie début  : {_fmt_eur(funds_start):>12}")
    print(f"  Trésorerie fin    : {_fmt_eur(funds_end):>12}")

    print(f"────────────────────────────────────────────────────────────────────────────\n")

    # --- Affichage bonus : pertes de clients ---
    losses = getattr(tr, "losses", None)
    if isinstance(losses, dict) and losses.get("lost_total", 0) > 0:
        print(f"\n  ⚠ Pertes clients : {losses['lost_total']}")
        print(f"     - Stock insuffisant : {losses['lost_stock']}")
        print(f"     - Capacité limitée  : {losses['lost_capacity']}")
        print(f"     - Autres raisons    : {losses['lost_other']}")

# ---------- (Optionnel) résumé multi-restos ----------

def print_multi_summary(rows: list) -> None:
    """
    Affiche un tableau compact pour plusieurs restaurants sur un tour.
    Chaque 'row' doit contenir au moins:
      name, ca, cogs, opex, result
    """
    if not rows:
        return
    print("\n================= Synthèse par restaurant =================")
    print(f"{'Restaurant':30} {'CA':>12} {'COGS':>12} {'OPEX':>12} {'Rés.opé.':>12}")
    print("-" * 84)
    for r in rows:
        name = str(r.get("name", ""))[:30]
        ca   = _fmt_eur(r.get("ca", 0.0))
        cogs = _fmt_eur(r.get("cogs", 0.0))
        opex = _fmt_eur(r.get("opex", 0.0))
        res  = _fmt_eur(r.get("result", 0.0))
        print(f"{name:30} {ca:>12} {cogs:>12} {opex:>12} {res:>12}")
    print("===========================================================\n")