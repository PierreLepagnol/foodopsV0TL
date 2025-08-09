# -*- coding: utf-8 -*-
from ..core.results import TurnResult

def print_turn_result(tr: TurnResult) -> None:
    print(f"\n===== Compte de Résultat - {tr.restaurant_name} - Tour {tr.tour} =====")
    print(f"Chiffre d'affaires        : {tr.ca:10.2f} €")
    print(f"Achats période            : {tr.achats_periode:10.2f} €")
    print(f"Variation de stock        : {tr.variation_stock:10.2f} €")
    print(f"Achats consommés          : {tr.achats_consommes:10.2f} €")
    print(f"Charges de personnel      : {tr.charges_personnel:10.2f} €")
    print(f"Charges fixes             : {tr.charges_fixes:10.2f} €")
    print(f"Marketing                 : {tr.marketing:10.2f} €")
    print(f"EBE                       : {tr.ebe:10.2f} €")
    print(f"Prêts (BPI+Banque)        : {tr.prets:10.2f} €")
    print(f"Résultat net              : {tr.resultat_net:10.2f} €")
    print(f"Trésorerie fin            : {tr.treso_fin:10.2f} €")
    print(f"Satisfaction RH           : {tr.rh_satisfaction:5.1f}/100")
    print(f"--- Activité ---")
    print(f"Clients attribués         : {tr.clients_attrib}")
    print(f"Clients servis            : {tr.clients_servis}")
    print(f"Prix médian               : {tr.prix_median:.2f} €")
