from ..domain.ingredient import Ingredient, IngredientCategory as C, FoodGrade as G

# Prix €/kg indicatifs (modifiables) — base France métropolitaine 2024–2025 (ordre de grandeur)
# NB: c’est un catalogue minimal pour démarrer. On l’augmentera ensuite.
INGREDIENTS_FR = {
    # Viandes
    "Poulet (filet)":   Ingredient("Poulet (filet)", 7.80,  C.VIANDE, G.G1_FRAIS_BRUT, 5),
    "Bœuf haché 15%":   Ingredient("Bœuf haché 15%", 9.50,  C.VIANDE, G.G1_FRAIS_BRUT, 4),
    "Steak (rumsteck)": Ingredient("Steak (rumsteck)", 17.0, C.VIANDE, G.G1_FRAIS_BRUT, 4),
    "Jambon blanc":     Ingredient("Jambon blanc", 8.40,    C.VIANDE, G.G4_CRU_PRET, 14),

    # Poissons
    "Saumon frais":     Ingredient("Saumon frais", 17.5, C.POISSON, G.G1_FRAIS_BRUT, 3),
    "Cabillaud":        Ingredient("Cabillaud", 14.0, C.POISSON, G.G1_FRAIS_BRUT, 3),

    # Légumes
    "Tomate":           Ingredient("Tomate", 2.80, C.LEGUME, G.G1_FRAIS_BRUT, 6),
    "Salade":           Ingredient("Salade", 1.90, C.LEGUME, G.G1_FRAIS_BRUT, 3),
    "Oignon":           Ingredient("Oignon", 1.20, C.LEGUME, G.G1_FRAIS_BRUT, 20),
    "Pomme de terre":   Ingredient("Pomme de terre", 1.40, C.LEGUME, G.G1_FRAIS_BRUT, 30),

    # Féculents
    "Pâtes (crues)":    Ingredient("Pâtes (crues)", 1.60, C.FECULENT, G.G2_CONSERVE, 365),
    "Riz (cru)":        Ingredient("Riz (cru)", 1.90, C.FECULENT, G.G2_CONSERVE, 365),

    # Produits laitiers
    "Mozzarella":       Ingredient("Mozzarella", 6.80, C.PRODUIT_LAITIER, G.G4_CRU_PRET, 10),
    "Comté":            Ingredient("Comté", 16.0, C.PRODUIT_LAITIER, G.G4_CRU_PRET, 30),
    "Beurre":           Ingredient("Beurre", 7.0,  C.PRODUIT_LAITIER, G.G2_CONSERVE, 120),

    # Boulangerie
    "Pain burger":      Ingredient("Pain burger", 3.50, C.BOULANGERIE, G.G5_CUIT_SOUS_VIDE, 5),
    "Baguette":         Ingredient("Baguette", 3.20, C.BOULANGERIE, G.G5_CUIT_SOUS_VIDE, 2),

    # Condiments
    "Huile":            Ingredient("Huile", 4.0,  C.CONDIMENT, G.G2_CONSERVE, 365),
    "Ketchup":          Ingredient("Ketchup", 2.2, C.CONDIMENT, G.G2_CONSERVE, 365),
    "Moutarde":         Ingredient("Moutarde", 4.5, C.CONDIMENT, G.G2_CONSERVE, 365),
}
