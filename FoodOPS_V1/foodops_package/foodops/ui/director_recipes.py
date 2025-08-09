# -*- coding: utf-8 -*-
from typing import List
from ..domain.restaurant import Restaurant
from ..data.ingredients import get_all_ingredients, Ingredient
from ..domain.simple_recipe import SimpleRecipe, Technique, Complexity
from ..rules.costing import recipe_cost_and_price

def _choose(prompt: str, max_i: int) -> int:
    try:
        v = int(input(prompt).strip())
        if 1 <= v <= max_i:
            return v
    except:
        pass
    return -1

def _fmt_money(x: float) -> str:
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def run_recipes_shop(r: Restaurant, current_tour: int) -> None:
    inv = r.inventory
    catalog = get_all_ingredients()

    while True:
        print("\n=== Recettes & Achats ===")
        print("1) Voir stock ingrédients")
        print("2) Acheter ingrédients (kg)")
        print("3) Produire des portions (recette simple)")
        print("4) Voir produits finis")
        print("5) Retour")
        ch = input("> ").strip()

        if ch == "1":
            if not inv.ingredients:
                print("Stock ingrédients: (vide)")
            else:
                print("Stock ingrédients (kg):")
                for (_, _), si in inv.ingredients.items():
                    print(f" - {si.ingredient.name} [{si.ingredient.grade.name}] : {si.kg:.2f} kg")

        elif ch == "2":
            # achat simple: choisir ingrédient exact (avec sa gamme) du catalogue
            print("\nCatalogue ingrédients:")
            for i, ing in enumerate(catalog, start=1):
                print(f"{i}) {ing.name} [{ing.grade.name}] — {_fmt_money(ing.base_price_eur_per_kg)}/kg")
            k = _choose("Sélection: ", len(catalog))
            if k == -1:
                print("Choix invalide.")
                continue
            ing = catalog[k-1]
            try:
                kg = float(input("Quantité (kg) à acheter: ").replace(",", "."))
                if kg <= 0:
                    print("Quantité invalide.")
                    continue
            except:
                print("Saisie invalide.")
                continue

            cost = round(ing.base_price_eur_per_kg * kg, 2)
            if r.funds < cost:
                print(f"Trésorerie insuffisante. Coût = {_fmt_money(cost)}, Fonds = {_fmt_money(r.funds)}")
                continue
            r.funds -= cost
            inv.add_ingredient(ing, kg)
            print(f"Acheté {kg:.2f} kg de {ing.name} [{ing.grade.name}] pour {_fmt_money(cost)}.")

        elif ch == "3":
            # Produire une recette simple à partir d'un ingrédient DISPONIBLE en stock
            if not inv.ingredients:
                print("Aucun ingrédient en stock.")
                continue

            # étape 1: choisir un nom d'ingrédient dispo
            names = sorted(set(n for (n, _g) in inv.ingredients.keys()))
            print("\nIngrédients disponibles (par nom):")
            for i, n in enumerate(names, start=1):
                print(f"{i}) {n}")
            kn = _choose("Nom: ", len(names))
            if kn == -1:
                print("Choix invalide.")
                continue
            name = names[kn-1]

            # étape 2: choisir la variante (gamme) en stock
            variants = inv.get_available_variants(name)
            print("\nVariantes en stock:")
            for i, si in enumerate(variants, start=1):
                print(f"{i}) {si.ingredient.name} [{si.ingredient.grade.name}] — {si.kg:.2f} kg dispo")
            kv = _choose("Variante: ", len(variants))
            if kv == -1:
                print("Choix invalide.")
                continue
            ing = variants[kv-1].ingredient

            # étape 3: définir la recette simple (technique + complexité + portion_kg)
            print("\nTechnique: 1) FROID  2) GRILLE  3) SAUTE  4) ROTI  5) FRIT  6) VAPEUR")
            kt = _choose("> ", 6)
            tech = [Technique.FROID, Technique.GRILLE, Technique.SAUTE, Technique.ROTI, Technique.FRIT, Technique.VAPEUR][kt-1]

            print("Complexité: 1) SIMPLE  2) COMPLEXE")
            kc = _choose("> ", 2)
            cplx = [Complexity.SIMPLE, Complexity.COMPLEXE][kc-1]

            try:
                portion_kg = float(input("Portion (kg/portion), ex 0.16: ").replace(",", "."))
                if portion_kg <= 0:
                    print("Portion invalide.")
                    continue
            except:
                print("Saisie invalide.")
                continue

            recipe_name = input("Nom de recette (ex: 'Burger bœuf', 'Saumon mi-cuit'): ").strip() or f"{name} - {tech.name.title()}"
            # on crée la recette simple
            recipe = SimpleRecipe.from_ingredient(recipe_name, ing, portion_kg, tech, cplx)
            # calcule prix conseillé selon type de resto
            cogs, price = recipe_cost_and_price(r.type, recipe)
            recipe.selling_price = price
            print(f"Prix conseillé: {_fmt_money(price)}  (COGS/portion ≈ {_fmt_money(cogs)})")

            try:
                portions = int(input("Portions à produire: ").strip())
                if portions <= 0:
                    print("Nombre invalide.")
                    continue
            except:
                print("Saisie invalide.")
                continue

            from ..rules.labour import recipe_prep_minutes_per_portion

            mins_per_portion = recipe_prep_minutes_per_portion(recipe)
            mins_need = int(round(mins_per_portion * portions))

            # vérifier la banque de minutes RH
            if r.rh_minutes_left <= 0:
                print("❌ Équipe saturée ce tour : plus de minutes de production disponibles.")
                continue

            if mins_need > r.rh_minutes_left:
                max_portions = max(0, r.rh_minutes_left // max(1, int(mins_per_portion)))
                if max_portions <= 0:
                    print("❌ Équipe saturée : impossible de produire davantage ce tour.")
                    continue
                print(f"⚠️ Capacité RH limite : production plafonnée à {max_portions} portions (au lieu de {portions}).")
                portions = max_portions
                mins_need = int(round(mins_per_portion * portions))

            # consomme minutes RH
            _ = r.consume_rh_minutes(mins_need)

            ok, cogs_total, msg = inv.produce_from_recipe(recipe, portions, current_tour)
            if not ok:
                print(f"❌ {msg}")
                continue

            # on mémorise le COGS du tour sur le restaurant (reconnaissance à la production)
            produced_cogs = getattr(r, "turn_cogs", 0.0)
            r.turn_cogs = round(produced_cogs + cogs_total, 2)
            # mémoriser “dernière recette utilisée” si tu veux la remettre dans r.menu aussi
            if all(rr.name != recipe.name for rr in r.menu):
                r.menu.append(recipe)

            print(f"✅ {msg}  | COGS reconnu ce tour: {_fmt_money(cogs_total)}")

        elif ch == "4":
            if not inv.finished:
                print("Aucun produit fini.")
            else:
                print("Produits finis (FIFO):")
                for b in inv.finished:
                    print(f" - {b.recipe_name} : {b.portions} portions, prix {_fmt_money(b.selling_price)}, péremption T{b.expiry_tour}")

        elif ch == "5":
            return

        else:
            print("Choix invalide.")
