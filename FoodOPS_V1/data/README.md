# FoodOPS — Configuration des Données

Ce répertoire contient les données de configuration principales qui alimentent le jeu de simulation de restaurant FoodOPS. Toutes les données sont stockées au format JSON pour faciliter l'édition et la validation.

## Vue d'ensemble

Les fichiers de données définissent les paramètres économiques, opérationnels et de gameplay qui façonnent l'expérience de simulation de restaurant. Ces configurations sont déclaratives et peuvent être modifiées pour ajuster l'équilibrage du jeu, ajouter du nouveau contenu ou personnaliser les scenarios sans changer le code principal du jeu.

## Structure des Fichiers et Objectifs

### 🥘 **catalog_config.json** - Catalogue des Ingrédients
Base de données complète des ingrédients définissant les produits alimentaires principaux disponibles dans la simulation.

**Structure pour chaque ingrédient :**
- `categories` : Catégories alimentaires (VIANDE, POISSON, LEGUME, FECULENT, PRODUIT_LAITIER, BOULANGERIE, CONDIMENT)
- `prices_by_grade` : Prix par niveau de qualité (G1_FRAIS_BRUT, G3_SURGELE)
- `perish_days` : Jours avant que l'ingrédient ne se gâte
- `fit_score` : Scores de compatibilité avec les concepts (FAST_FOOD, BISTRO, GASTRO) de 0.0 à 1.0
- `tier` : Niveau de disponibilité (ALL, BISTRO+, GASTRO_ONLY)

**Exemples :**
- Ingrédients premium (Truffe noire, Homard) exclusifs au concept GASTRO
- Produits de base polyvalents (Poulet, Pomme de terre) disponibles pour tous les concepts
- Niveaux de qualité affectant à la fois le prix et la pertinence du gameplay

### 🎯 **concept_fit.json** - Préférences des Segments de Clientèle
Définit à quel point chaque concept de restaurant séduit les différentes démographies de clients.

**Structure :**
- Concepts de restaurant : `FAST_FOOD`, `BISTRO`, `GASTRO`
- Segments de clientèle : `etudiant`, `actif`, `famille`, `touriste`, `senior`
- Scores d'adéquation : 0.0-1.0 représentant le niveau d'attrait

**Impact sur le Gameplay :**
- Scores plus élevés = plus attractif pour ce segment
- Utilisé dans les calculs de flux client et de positionnement marché

### 🏢 **local_config.json** - Emplacements de Restaurant
Propriétés de restaurant disponibles avec leurs caractéristiques et coûts.

**Propriétés par emplacement :**
- `nom` : Nom et description de l'emplacement
- `surface` : Mètres carrés de surface au sol
- `capacite_clients` : Maximum de clients simultanés
- `loyer` : Coût de loyer mensuel
- `prix_fond` : Prix d'achat/caution de bail
- `visibilite` : Multiplicateur de visibilité de l'emplacement (affecte la découverte client)

**Exemples :**
- "Kiosque Campus" : Petit, abordable, orienté étudiants
- "Quartier Chic" : Emplacement premium avec haute visibilité et coûts élevés

### 👥 **roles.json** - Postes du Personnel et Économie
Définit les rôles du personnel disponibles, leurs coûts et impact opérationnel par concept de restaurant.

**Structure par rôle :**
- `nom` : Titre du poste
- `categorie` : Département (direction, cuisine, salle)
- `restaurant_types` : Paramètres spécifiques au concept :
  - `salaire_marche` : Salaire marché mensuel
  - `capacite_couverts` : Capacité de service (couverts par période)
  - `impact_qualite` : Facteur d'amélioration qualité (0.0-1.0)

**Catégories de Rôles :**
- **Direction** : Rôles de management avec supervision de haut niveau
- **Cuisine** : Personnel de cuisine du Commis au Chef étoilé
- **Salle** : Postes de service en salle

### 🌍 **scenarios.json** - Scénarios de Marché
Environnements de marché pré-configurés avec compositions démographiques.

**Chaque scénario définit :**
- `name` : Nom descriptif du scénario
- `population_total` : Base totale de clientèle potentielle
- `segments_share` : Répartition en pourcentage par segment client
- `note` : Conseils de stratégie gameplay

**Scénarios disponibles :**
- `quartier_etudiant` : Zone à forte densité étudiante (sensible au prix, gros volume)
- `centre_ville` : Mix urbain équilibré
- `zone_touristique` : Orienté touristes (axé expérience, moins sensible au prix)

### 💰 **segment_clients.json** - Segments de Clientèle
Profils économiques et comportementaux pour différents types de clients.

**Par segment :**
- `budget_moyen` : Budget de dépense moyen par visite
- `description` : Caractéristiques comportementales et économiques

**Segments :**
- `etudiant` : Étudiants soucieux du budget (€10 en moyenne)
- `actif` : Professionnels actifs recherchant la praticité (€18 en moyenne)
- `famille` : Groupes familiaux avec commandes plus importantes (€55 en moyenne)
- `touriste` : Visiteurs recherchant l'expérience (€28 en moyenne)
- `senior` : Clients âgés privilégiant le service (€20 en moyenne)

## Relations entre Données et Flux de Jeu

### Modèle Économique
1. **Segments clients** définissent le pouvoir d'achat et les préférences
2. **Adéquation concept** détermine l'attrait pour chaque segment
3. **Emplacement** affecte la visibilité et les coûts
4. **Rôles du personnel** déterminent la capacité de service et la qualité
5. **Catalogue ingrédients** fournit la structure de coûts et les options qualité

### Stratégie Qualité et Prix
- **Scores d'adéquation ingrédients** pénalisent les choix inappropriés (ex: fast food utilisant des ingrédients premium)
- **Impact personnel** améliore la qualité de service et la capacité
- **Visibilité emplacement** multiplie la découverte client
- **Contraintes budgétaires** des segments clients limitent la flexibilité tarifaire

## Directives de Configuration

### Considérations d'Équilibrage
- **Réalisme économique** : Salaires, loyers et coûts alimentaires doivent refléter des ratios réalistes
- **Chemins de progression** : Assurer que des stratégies viables existent pour chaque type de concept
- **Variété de choix** : Fournir des compromis significatifs entre coût, qualité et capacité

### Meilleures Pratiques de Modification
1. **Maintenir l'intégrité des données** : S'assurer que toutes les clés référencées existent dans tous les fichiers
2. **Tester les changements d'équilibrage** : De petits ajustements peuvent impacter significativement le gameplay
3. **Documenter les changements** : Garder des notes sur les modifications d'équilibrage pour référence future
4. **Sauvegarder les configurations** : Sauver les configurations fonctionnelles avant des changements majeurs

### Points d'Extension
- **Nouveaux ingrédients** : Ajouter à `catalog_config.json` avec des scores d'adéquation appropriés
- **Nouveaux emplacements** : Étendre `local_config.json` avec différents profils économiques
- **Nouveaux scénarios** : Créer des mix démographiques dans `scenarios.json`
- **Nouveaux rôles** : Ajouter des postes spécialisés à `roles.json`
- **Nouveaux segments** : Définir de nouveaux types de clients dans `segment_clients.json`

## Notes Techniques

### Validation des Données
- Tous les fichiers JSON doivent valider contre leurs schémas implicites
- Les valeurs numériques doivent rester dans des plages réalistes
- Les clés texte doivent être cohérentes entre les fichiers qui les référencent

### Considérations de Performance
- Les données sont chargées à l'initialisation du jeu
- Les recherches runtime sont fréquentes, donc la stabilité des clés est importante
- Les gros catalogues peuvent impacter l'usage mémoire

### Préparation à la Localisation
- Les champs texte (noms, descriptions) peuvent être externalisés pour traduction
- Les paramètres numériques restent culture-neutres


