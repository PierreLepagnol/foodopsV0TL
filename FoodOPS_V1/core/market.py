"""
Moteur d'allocation de la demande (réaliste) pour FoodOps.

Règles implémentées :
- La demande vient d'un Scenario (population totale + parts par segments).
- Choix d'un restaurant (pas d'un “type” abstrait) en fonction d'un score d'attraction.
- Filtre budget dur : si prix médian du restaurant > budget segment x tolérance => restaurant inéligible.
- Capacité exploitable par tour = capacité brute x coefficient de vitesse (par type de restaurant).
- Redistribution en cas de saturation : on passe au 2e, 3e meilleur, etc.
- Clients perdus si aucun restaurant éligible ou plus de capacité.
- Cannibalisation douce : si plusieurs restaurants d'un même type, légère pénalité de score.

Retour :
    allocate_demand(...) -> dict {index_restaurant: clients_attribués}

NB : Les clients “perdus” ne sont pas retournés ici, mais on expose
     une fonction optionnelle `estimate_lost_customers(...)` si besoin plus tard.
"""

from collections import Counter
from math import sqrt
from typing import Dict, List, Tuple

import numpy as np

from FoodOPS_V1.domain import Restaurant, RestaurantType
from FoodOPS_V1.domain.market import BUDGET_PER_SEGMENT, Segment
from FoodOPS_V1.domain.scenario import Scenario
from FoodOPS_V1.rules.scoring import attraction_score

# ------------------------------
# Paramètres “marché” (ajustables)
# ------------------------------


# Pénalité “cannibalisation” : plus il y a de restaurants d'un même type, plus on pénalise légèrement le score.
# Ex: factor = 1 / sqrt(1 + alpha*(n_same_type-1))


# ------------------------------
# Petits shims & helpers
# ------------------------------


def is_eligible_by_budget(restaurant: Restaurant, customer: Segment) -> bool:
    """Vrai si le prix médian du menu est compatible avec le budget du segment."""
    # Tolérance budget (ex: 1.20 => 20% au-dessus du budget moyen toléré)
    budget_tolerance: float = 1.20

    menu = restaurant.menu
    prix_des_items = [item.price for item in menu if item is not None]
    price = np.median(prix_des_items) if prix_des_items else 0.0

    budget = BUDGET_PER_SEGMENT.get(customer, 15.0)  # default budget
    return price <= budget * budget_tolerance


def count_restaurants_types(restaurants: List[Restaurant]) -> Dict[RestaurantType, int]:
    """
    Compte le nombre de restaurants par type pour calculer la cannibalisation.

    Cette fonction analyse la composition du marché pour identifier les situations
    de concurrence directe entre restaurants du même type (ex: plusieurs fast-foods).
    Le résultat est utilisé par _cannibalization_factor() pour appliquer une pénalité
    douce aux scores d'attraction quand plusieurs établissements similaires se
    disputent le même segment de clientèle.

    Args:
        restaurants: Liste des restaurants actifs sur le marché

    Returns:
        Dictionnaire mapping chaque RestaurantType vers son nombre d'occurrences.

    Example:
        Si on a 2 fast-foods, 1 bistro et 1 gastro:
        {"FAST_FOOD": 2, "BISTRO": 1, "GASTRO": 1}
    """
    return Counter(r.type for r in restaurants)


def cannibalization_factor(
    restaurant: Restaurant, counts_by_type: Dict[RestaurantType, int]
) -> float:
    """Calcule le facteur de pénalisation pour la cannibalisation entre restaurants du même type.

    Lorsque plusieurs restaurants du même type (ex: plusieurs fast-foods) sont présents
    sur le marché, ils se disputent la même clientèle cible, ce qui réduit l'efficacité
    de chacun. Cette fonction applique une pénalité douce qui augmente avec le nombre
    de concurrents directs.

    La formule utilisée est: 1 / max(1, sqrt(1 + cannibalization_alpha * (n - 1)))
    où n est le nombre de restaurants du même type que 'restaurant'.

    Args:
        restaurant: Restaurant pour lequel calculer le facteur de cannibalisation
        counts_by_type: Dictionnaire contenant le nombre de restaurants par type
                       sur le marché (généré par count_restaurants_types)

    Returns:
        Facteur multiplicateur entre 0 et 1:
        - 1.0 si le restaurant est seul de son type (aucune cannibalisation)
        - < 1.0 si plusieurs restaurants du même type existent (pénalité croissante)

    Examples:
        - 1 seul fast-food: facteur = 1.0 (aucune pénalité)
        - 2 fast-foods: facteur ≈ 0.8-0.9 (pénalité légère)
        - 3+ fast-foods: facteur diminue progressivement

    Note:
        Le paramètre cannibalization_alpha contrôle l'intensité de la pénalisation.
        Une valeur plus élevée augmente l'impact de la cannibalisation.
    """
    cannibalization_alpha: float = 0.50

    # Récupère le nombre de restaurants du même type que 'restaurant'
    n = counts_by_type[restaurant.type]

    # Si le restaurant est seul de son type, aucune cannibalisation
    if n <= 1:
        return 1.0

    # Applique une pénalité douce basée sur la racine carrée
    # Plus n est grand, plus le facteur diminue (mais jamais en dessous de 0)
    return 1.0 / max(1.0, sqrt(1.0 + cannibalization_alpha * (n - 1)))


def _ranked_for_segment(
    restaurants: List[Restaurant],
    segment: Segment,
    counts_by_type: Dict[RestaurantType, int],
) -> List[Tuple[int, float]]:
    """
    Classe les restaurants par ordre d'attractivité décroissante pour un segment de clientèle donné.

    Cette fonction évalue chaque restaurant selon sa capacité à attirer un segment spécifique
    de clients en tenant compte de :
    - La compatibilité budgétaire (les restaurants trop chers sont exclus)
    - Le score d'attraction de base (visibilité, menu, etc.)
    - Les pénalités de cannibalisation (concurrence entre restaurants du même type)

    Args:
        restaurants: Liste des restaurants à évaluer et classer
        segment: Nom du segment de clientèle (ex: "étudiant", "famille", "touriste")
        counts_by_type: Comptage des restaurants par type pour calculer la cannibalisation

    Returns:
        Liste de tuples (index_restaurant, score_final) triée par score décroissant.
        Seuls les restaurants éligibles (compatibles budgétairement) sont inclus.

    Example:
        >>> _ranked_for_segment(restaurants, "étudiant", {RestaurantType.BISTRO: 2})
        [(0, 8.5), (2, 6.2), (1, 3.1)]  # Restaurant 0 le plus attractif pour les étudiants
    """
    unranked: Dict[int, float] = {}

    # Évalue chaque restaurant pour ce segment spécifique
    for index_restaurant, restaurant in enumerate(restaurants):
        # Filtre les restaurants incompatibles budgétairement
        if not is_eligible_by_budget(restaurant, segment):
            continue

        # Calcule le score d'attraction de base (sans pénalités)
        base_score = attraction_score(restaurant, segment)

        # Applique la pénalité de cannibalisation si plusieurs restaurants du même type
        penal = cannibalization_factor(restaurant, counts_by_type)

        # Score final = score de base × facteur de pénalisation
        unranked[index_restaurant] = base_score * penal

    # Trie par score décroissant (les meilleurs restaurants en premier)
    # ranked.sort(key=lambda x: x[1], reverse=True)
    # ranked = sorted(unranked.items(), key=lambda x: x[1], reverse=True)

    return unranked


# ------------------------------
# API principale
# ------------------------------


def allocate_demand(
    restaurants: List[Restaurant], scenario: Scenario
) -> Dict[int, int]:
    """
    Alloue la demande client aux restaurants selon une dynamique de marché réaliste.

    Cette fonction simule la façon dont les clients choisissent les restaurants en :
    1. Décomposant la demande totale par segments de clientèle (étudiants, familles, etc.)
    2. Pour chaque segment, classant les restaurants par score d'attraction et compatibilité budgétaire
    3. Allouant les clients avec une approche gloutonne : remplit d'abord le meilleur restaurant,
       puis fait déborder vers le suivant quand la capacité est atteinte
    4. Appliquant des pénalités de cannibalisation quand plusieurs restaurants du même type sont en concurrence

    Args:
        restaurants: Liste d'objets Restaurant auxquels allouer la demande
        scenario: Scénario contenant les données de population et de segments de marché

    Returns:
        Dict mappant l'index du restaurant au nombre de clients alloués à ce restaurant.
        Exemple : {0: 45, 1: 23, 2: 0} signifie que le restaurant 0 reçoit 45 clients,
                  le restaurant 1 en reçoit 23, le restaurant 2 n'en reçoit aucun.

    Note:
        - Les clients sont "perdus" si aucun restaurant n'est compatible budgétairement pour leur segment
        - Les clients sont "perdus" si tous les restaurants compatibles sont à capacité
        - Les clients perdus ne sont pas suivis dans la valeur de retour mais peuvent être estimés
          en utilisant estimate_lost_customers()
    """
    # Convertit les parts de marché du scénario en quantités réelles de clients par segment
    demand_by_segments = scenario.compute_segment_quantities()
    counts_by_type = count_restaurants_types(restaurants)

    # Initialise le suivi de capacité - combien de clients chaque restaurant peut encore servir
    capacity_left_per_restaurant = {
        index_restaurant: restaurant.compute_exploitable_capacity()
        for index_restaurant, restaurant in enumerate(restaurants)
    }
    # Initialise le suivi d'allocation - combien de clients assignés à chaque restaurant
    allocated = {index_restaurant: 0 for index_restaurant, _ in enumerate(restaurants)}

    # Traite chaque segment de clientèle indépendamment
    for segment, quantity in demand_by_segments.items():
        if quantity <= 0:
            continue

        # Obtient les restaurants classés par attractivité pour ce segment
        # (inclut le filtrage budgétaire et les pénalités de cannibalisation)
        ranked = _ranked_for_segment(restaurants, segment, counts_by_type)

        # Si aucun restaurant n'est compatible budgétairement pour ce segment, tous les clients sont perdus
        if not ranked:
            continue
        remaining = quantity

        # Allocation gloutonne : remplit d'abord le restaurant le mieux classé, puis déborde
        # vers le suivant quand la capacité est atteinte
        for index_restaurant, _score in ranked:
            if remaining <= 0:
                break
            if capacity_left_per_restaurant[index_restaurant] <= 0:
                continue

            # Alloue autant de clients que possible à ce restaurant
            take = min(remaining, capacity_left_per_restaurant[index_restaurant])
            allocated[index_restaurant] += take
            capacity_left_per_restaurant[index_restaurant] -= take
            remaining -= take

    return allocated


def clamp_capacity(
    restaurants: List[Restaurant], allocated: Dict[int, int]
) -> Dict[int, int]:
    """Limite l'allocation de clients par la capacité exploitable de chaque restaurant.

    Cette fonction applique une contrainte de capacité physique sur l'allocation de clients
    calculée par allocate_demand(). Elle garantit qu'aucun restaurant ne se voit attribuer
    plus de clients qu'il ne peut physiquement servir selon sa capacité exploitable.

    Args:
        restaurants: Liste des restaurants du jeu avec leurs caractéristiques
        allocated: Dictionnaire {index_restaurant: nombre_clients} résultant de l'allocation
                  de la demande par segment de clientèle

    Returns:
        Dictionnaire {index_restaurant: nombre_clients_servis} où chaque valeur est
        bornée par la capacité exploitable du restaurant correspondant

    Note:
        - La capacité exploitable est calculée par restaurant.compute_exploitable_capacity()
        - Cette fonction est typiquement appelée après allocate_demand() dans le cycle de jeu
        - Les clients non servis par manque de capacité constituent une perte de type "capacity"

    Example:
        Si allocated = {0: 1500, 1: 800} et que les capacités exploitables sont
        {0: 1200, 1: 1000}, alors le résultat sera {0: 1200, 1: 800}
    """
    served: Dict[int, int] = {}
    for index_restaurant, restaurant in enumerate(restaurants):
        cap = restaurant.compute_exploitable_capacity()
        served[index_restaurant] = min(allocated.get(index_restaurant, 0), cap)
    return served
