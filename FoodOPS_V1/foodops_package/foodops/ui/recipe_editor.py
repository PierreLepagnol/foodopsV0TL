from typing import List, Dict
from ..domain.recipe import Recipe, RecipeLine, PrepStep
from ..domain.ingredient import Ingredient
from ..data.ingredients_fr import INGREDIENTS_FR
from ..rules import costing
from ..domain.restaurant import RestaurantType


def pick_policy_for_restotype(rt: RestaurantType) -> costing.PricePolicy:
    if rt == RestaurantType.FAST_FOOD:
        return costing.FAST_POLICY
    if rt == RestaurantType.GASTRO:
        return costing.GASTRO_POLICY
    return costing.BISTRO_POLICY


def choose_ingredients() -> List[Ingredient]:
    """Sélection multi simple depuis le catalogue FR."""
    names = list(INGREDIENTS_FR.keys())
    print("\nCatalogue ingrédients (FR) 🍅🥕 :")
    for i, n in enumerate(names, 1):
        ing = INGREDIENTS_FR[n]
        print(f" {i:>2}. {n} — {ing.base_price_eur_per_kg:.2f} €/kg, grade={ing.grade.name}")
    print("Tapez les numéros séparés par des virgules (ex: 1,3,5) ou Enter pour annuler. 📝")
    raw = input("> ").strip()
    if not raw:
        return []
    idxs = []
    for part in raw.split(","):
        try:
            j = int(part.strip())
            if 1 <= j <= len(names):
                idxs.append(j - 1)
        except ValueError:
            pass
    return [INGREDIENTS_FR[names[j]] for j in idxs]


def build_recipe(rt: RestaurantType) -> Recipe | None:
    print("\n=== Création d'une recette === 🍽️")
    name = input("Nom de la recette : ").strip()
    if not name:
        print("❌ Annulé.")
        return None

    ings = choose_ingredients()
    if not ings:
        print("❌ Aucun ingrédient sélectionné. Annulé.")
        return None

    lines: List[RecipeLine] = []
    for ing in ings:
        while True:
            try:
                qty = float(input(f"Quantité de {ing.name} (en grammes, ex 120) : "))
                if qty <= 0: raise ValueError
                break
            except ValueError:
                print("⚠️ Veuillez entrer un nombre positif.")
        # Étapes de prep (V1 raccourci)
        prep = []
        ans = input("Parage/cuisson ? (o/N) : ").strip().lower()
        if ans == "o":
            while True:
                try:
                    lr = float(input("  Perte (%) ex 10 pour -10% (Enter pour terminer) : ") or "NaN")
                    if lr != lr:  # NaN -> break
                        break
                    prep.append(PrepStep(name="loss", loss_ratio=lr/100.0))
                except ValueError:
                    break
        lines.append(RecipeLine(ingredient=ing, qty_g=qty, prep=prep))

    while True:
        try:
            portions = int(input("Nombre de portions (rendement) : "))
            if portions <= 0: raise ValueError
            break
        except ValueError:
            print("⚠️ Nombre invalide.")

    r = Recipe(name=name, lines=lines, yield_portions=portions)

    # Calculs
    cost = r.cost_per_portion()
    q = r.estimate_quality()
    policy = pick_policy_for_restotype(rt)
    suggested = r.suggest_price(policy)

    print("\n--- Fiche coût express --- 💶 ---")
    print(f"Recette : {r.name} 🍽️")
    print(f"Coût matières / portion : {cost:.2f} €")
    print(f"Qualité estimée (0..1) : {q:.2f} ⭐")
    print(f"Prix conseillé ({policy.name}) : {suggested:.2f} € 💡")
    ans = input("Fixer un prix de vente maintenant ? (Enter = conseillé / valeur = prix €) : ").strip()
    if ans:
        try:
            r.selling_price = max(0.0, float(ans))
        except ValueError:
            r.selling_price = suggested
    else:
        r.selling_price = suggested

    # base_quality utilisé par le moteur actuel (scoring déjà en place)
    r.base_quality = q
    print(f"Prix de vente retenu : {r.selling_price:.2f} € ✅")
    return r


def edit_menu_interactive(resto_type: RestaurantType) -> List[Recipe]:
    print("\n=== Éditeur de recettes — Construction du menu === 🧑‍🍳")
    menu: List[Recipe] = []
    while True:
        r = build_recipe(resto_type)
        if r:
            menu.append(r)
        more = input("Ajouter une autre recette ? (o/N) : ").strip().lower()
        if more != "o":
            break
    if not menu:
        print("Menu vide — pensez à utiliser les menus par défaut si besoin. ⚠️")
    return menu
