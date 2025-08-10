# Couche Domaine FoodOPS

Objets métier fondamentaux pour le jeu de simulation de restaurant.

## Vue d'ensemble

La couche domaine contient des objets de données purs qui modélisent les restaurants, ingrédients, recettes, personnel et scénarios de marché. Ces objets se concentrent sur la représentation des données sans logique métier complexe.

## Objets Principaux

### Gestion du Restaurant
- **`Restaurant`** - Entité principale avec finances, personnel, menu, inventaire et métriques de performance
- **`Local`** - Emplacement du restaurant avec capacité, loyer et propriétés de visibilité
- **`RestaurantType`** - Enum : `FAST_FOOD`, `BISTRO`, `GASTRO`

### Menu et Recettes
- **`SimpleRecipe`** - Plat du menu avec ingrédients, technique, complexité et tarification
- **`Recipe`** - Modèle de recette avancé avec étapes de préparation détaillées (usage futur)
- **`Technique`** - Méthodes de cuisson : `FROID`, `GRILLE`, `SAUTE`, `FOUR`, `FRIT`, `VAPEUR`
- **`Complexity`** - Difficulté de la recette : `SIMPLE`, `COMPLEXE`, `COMBO`

### Ingrédients et Inventaire
- **`Ingredient`** - Produits alimentaires avec catégories, grades et tarification
- **`IngredientCategory`** - Types : `VIANDE`, `POISSON`, `LEGUME`, `FECULENT`, etc.
- **`FoodGrade`** - Niveaux de qualité : `G1_FRAIS_BRUT` à `G5_CUIT_SOUS_VIDE`
- **`Inventory`** - Gestion des stocks avec consommation FIFO et suivi des dates d'expiration

### Personnel et Opérations
- **`Employe`** - Membre du personnel avec rôle, salaire et productivité
- **`Role`** - Types de postes : `SERVEUR`, `CUISINIER`, `MANAGER`
- Banques de minutes service/cuisine pour la capacité opérationnelle

### Marché et Scénarios
- **`Scenario`** - Conditions de marché avec population et segments de clientèle
- **`Segment`** - Types de clients : `ETUDIANT`, `ACTIF`, `FAMILLE`, `TOURISTE`, `SENIOR`

## Fonctionnalités Clés

- **Inventaire FIFO** - Consommation automatique des ingrédients et vente des produits par date d'expiration
- **Ingrédients Multi-Grades** - Différents niveaux de qualité affectent le coût et la perception client
- **Productivité du Personnel** - Allocation de minutes basée sur le rôle pour les opérations de service et cuisine
- **Modélisation des Coûts** - Calcul du coût de base avec multiplicateurs de grade et facteurs de main-d'œuvre

## Principes de Conception

- **Centré sur les Données** - Logique métier minimale, focus sur la représentation d'état
- **Sérialisable** - Tous les objets peuvent être sauvegardés/chargés depuis JSON
- **Immutable Autant que Possible** - Privilégier les fonctions pures plutôt que la mutation d'état
- **Séparation Claire** - Les règles métier vivent dans `rules/`, l'orchestration dans `core/`
