# foodops/ui/results_view.py

from FoodOPS_V1.domain.types import TurnResult


# ---------- Helpers de formatage ----------


def format_to_euro(x: float) -> str:
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


# ---------- Impression d'un tour ----------


def print_turn_result(resultat_tour: TurnResult) -> None:
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

    name = resultat_tour.restaurant_name
    tour = resultat_tour.tour

    # Demande & capacité
    clients_attr = _num(resultat_tour.clients_attr)
    clients_serv = _num(resultat_tour.clients_serv)
    capacity = _num(resultat_tour.capacity)

    # Prix & ventes
    price_med = float(resultat_tour.price_med)
    ca = float(resultat_tour.ca)
    cogs = float(resultat_tour.cogs)

    # OPEX
    fixed_costs = float(resultat_tour.fixed_costs)
    marketing = float(resultat_tour.marketing)
    rh_cost = float(resultat_tour.rh_cost)

    funds_start = float(resultat_tour.funds_start)
    funds_end = float(resultat_tour.funds_end)

    # KPIs dérivés
    asp = ca / clients_serv if clients_serv > 0 else price_med
    gross_margin = ca - cogs
    opex = fixed_costs + marketing + rh_cost
    operating_result = gross_margin - opex

    # Barres
    cap_bar = _bar(clients_serv, max(1, capacity))
    dem_bar = _bar(clients_serv, max(1, clients_attr))

    print(
        f"\n────────────────────────────────────────────────────────────────────────────"
    )
    print(f"  📊 Résultat — {name} — Tour {tour}")
    print(
        f"────────────────────────────────────────────────────────────────────────────"
    )

    # Ligne demande/capacité
    print(
        f"  Demande attribuée : {clients_attr:>6d}   Couvert(s) servi(s) : {clients_serv:>6d}"
    )
    print(
        f"  Capacité RH/salle : {capacity:>6d}   Utilisation capacité : {_pct(clients_serv, capacity):>6}"
    )
    print(f"  Couverture demande: {_pct(clients_serv, clients_attr):>6}")
    print(f"  [{cap_bar}] Capacité")
    print(f"  [{dem_bar}] Demande  ")

    # Prix & CA
    print(
        f"\n  Prix médian menu : {format_to_euro(price_med):>12}   Ticket moyen (réel) : {format_to_euro(asp):>12}"
    )
    print(f"  Chiffre d'affaires: {format_to_euro(ca):>12}")

    # COGS & marge
    print(f"  COGS (coût prod)  : {format_to_euro(cogs):>12}")
    print(
        f"  Marge brute       : {format_to_euro(gross_margin):>12}   (taux: {_pct(gross_margin, ca)})"
    )

    # OPEX
    print(f"\n  Coûts fixes       : {format_to_euro(fixed_costs):>12}")
    print(f"  Marketing         : {format_to_euro(marketing):>12}")
    print(f"  Masse salariale   : {format_to_euro(rh_cost):>12}")
    print(f"  OPEX total        : {format_to_euro(opex):>12}")

    # Résultat opé
    print(f"\n  Résultat opé.     : {format_to_euro(operating_result):>12}")

    # Tréso
    print(f"\n  Trésorerie début  : {format_to_euro(funds_start):>12}")
    print(f"  Trésorerie fin    : {format_to_euro(funds_end):>12}")

    print(
        f"────────────────────────────────────────────────────────────────────────────\n"
    )

    # --- Affichage bonus : pertes de clients ---
    losses = resultat_tour.losses
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
        ca = format_to_euro(r.get("ca", 0.0))
        cogs = format_to_euro(r.get("cogs", 0.0))
        opex = format_to_euro(r.get("opex", 0.0))
        res = format_to_euro(r.get("result", 0.0))
        print(f"{name:30} {ca:>12} {cogs:>12} {opex:>12} {res:>12}")
    print("===========================================================\n")
