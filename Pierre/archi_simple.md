# ✅ Checklist (architecture, haut niveau)

1. **Définir le cycle de tour** (états, fenêtres d’actions, règles de résolution, conditions de fin).
2. **Spécifier les contrats** entre composants (DTO d’`Action`, `GameState`, `Event` + erreurs).
3. **Séparer les responsabilités** : Moteur (logique pure), UI (I/O), Persistance (stockage & requêtes).
4. **Choisir le flux**: append-only des actions + snapshot de l’état à chaque tour (simple & robuste).
5. **Concurrence & cohérence** : verrous/logique idempotente, horodatage, contrôle d’accès.
6. **Diffusion d’événements** : notifications en temps réel (WebSocket) + REST pour lecture/écriture.
7. **Tests & évolutivité** : logique testable (pure), services stateless, DB indexée.

# ✅ Checklist ciblée (moteur FoodOPS)

- **Cycle de tour concret aligné avec `FoodOPS_V1.core.game.Game.play()`** :
  1. Péremption produits finis (`resto.inventory.cleanup_expired(current_tour)`)
  2. Reset minutes RH (`resto.reset_rh_minutes()`)
  3. Allocation demande marché (`allocate_demand(restaurants, scenario)`)
  4. Limitation capacité (`clamp_capacity(restaurants, attrib)`)
  5. Contraintes service minutes (`_service_capacity_with_minutes()`) + stock fini (`get_available_portions()`)
  6. Ventes FIFO (`_sell_from_finished_fifo()`) + consommation minutes (`_consume_service_minutes()`)
  7. Calcul pertes clients (`_apply_client_losses()`) + impact notoriété
  8. Écritures comptables (ventes, COGS, charges fixes, marketing, masse salariale, amortissements)
  9. Gestion emprunts BPI/banque (`split_interest_principal()`) + posts comptables
  10. Mise à jour trésorerie finale + reset COGS production + satisfaction RH

- **Contrats d'actions spécifiques FoodOPS** :
  - `DirectorOfficeAction` : équipe RH, marketing_budget, equipment_upgrade, menu_changes
  - `ProductionAction` : recipes_to_produce, quantities, raw_materials_purchase
  - `TurnResult` exposable : clients_attribues, clients_serv, capacity, price_med, ca, cogs, fixed_costs, marketing, rh_cost, funds_start/end, losses
  - Actions validées par phase : "DIRECTOR_OFFICE" --> "PRODUCTION" --> "RESOLVE" --> "DISPLAY_RESULTS"

- **Ports/Adapters précis FoodOPS** :
  - `ActionRepository` : append-only des actions joueurs avec `actionId` unique + `gameId` + `playerId` + `turn`
  - `GameStateRepository` : snapshots complets après chaque tour résolu (restaurants + inventaires + scenario state)
  - `EventOutbox` : diffusion `TurnResult`, pertes clients, faillites, fin de partie
  - `AccountingAdapter` : posts comptables vers `Ledger` avec audit trail
  - `ScenarioAdapter` : lecture paramètres marché + évolution dynamique population/segments

- **Snapshot d'état par tour spécifique FoodOPS** :
  - Restaurants : name, type, funds, notoriety, monthly_bpi/bank, bpi/bank_outstanding, equipment_invest
  - Inventaires : raw_materials (nom, quantity, unit_cost), finished (portions, selling_price, production_tour, expiry_tour)
  - Équipes RH : positions, satisfaction, service_minutes_left, monthly_cost
  - Comptabilité : balance_accounts(upto_tour) pour bilan + compte de résultat
  - Marché : population mensuelle, shares par segment, allocation précédente
  - KPI : capacité utilisée, taux de perte clients, évolution trésorerie, ROI équipement

- **Règles déterministes & idempotence FoodOPS** :
  - Fonctions pures critiques : `allocate_demand()`, `clamp_capacity()`, `_service_capacity_with_minutes()`, `_sell_from_finished_fifo()`, `split_interest_principal()`
  - Idempotence via `actionId` unique : rejeter doublons, recompute déterministe si replay d'actions
  - Seed fixe pour allocation aléatoire marché par (gameId, turn)
  - FIFO strict sur inventaire fini : ordre insertion préservé, pas d'ambiguïté
  - Calculs financiers : arrondi à 2 décimales, ordre opérations fixe

- **Tests unitaires ciblés sur fonctions pures critiques** :
  - Marché : `allocate_demand()` avec différents scénarios population/segments, `clamp_capacity()` avec contraintes variées
  - Inventaire : `_sell_from_finished_fifo()` avec lots multiples/vides, `cleanup_expired()` avec tours variables
  - Minutes service : `_service_capacity_with_minutes()` + `_consume_service_minutes()` selon type restaurant
  - Emprunts : `split_interest_principal()` avec différents taux/durées, soldes en cours
  - Scénario : évolution déterministe population, parsing paramètres marché
  - Comptabilité : posts standards, balance accounts, cohérence bilan/résultat

# 🎯 Objectif d’architecture (simple, découplée)

Trois blocs **indépendants** reliés par des **contrats** stables :

* **Moteur de jeu** : valide les actions, résout un tour, produit le nouvel état + événements.
* **Interface utilisateur (UI)** : collecte les actions des joueurs, affiche l’état/les résultats.
* **Base de données (DB)** : source de vérité (actions append-only) + snapshots d’état par tour.

Communication principale : **REST/JSON** (lecture/écriture) + **WebSocket** (push d’événements).
Le moteur **ne connaît pas** l’UI ; il parle en `DTO` et écrit dans la DB / publie des `Event`.

# 🧩 Contrats (DTO) – version initiale

```txt
ActionDTO {
  actionId: UUID
  gameId: UUID
  playerId: UUID
  turn: int
  type: string          // "MOVE", "ATTACK", ...
  payload: JSON         // paramètres spécifiques
  submittedAt: ISO-8601
  clientVersion?: string
}

ValidationError {
  code: string          // "INVALID_STATE", "NOT_YOUR_TURN", ...
  message: string
  details?: JSON
}

GameStateDTO {
  gameId: UUID
  turn: int
  phase: "COLLECT" | "RESOLVE" | "ENDED"
  players: [ { playerId, publicState: JSON } ]
  world: JSON           // état global
  lastUpdatedAt: ISO-8601
}

EventDTO {
  eventId: UUID
  gameId: UUID
  turn: int
  kind: "ACTION_ACCEPTED" | "ACTION_REJECTED" | "TURN_RESOLVED" | "GAME_ENDED"
  payload: JSON         // diffs, logs, etc.
  publishedAt: ISO-8601
}
```

# 🔖 Contrats FoodOPS (actions & résultats)

Spécialisation des contrats pour FoodOPS.

```txt
ActionDTO {
  actionId: UUID
  gameId: UUID
  playerId: UUID
  turn: int
  type: "HR_RECRUIT" | "HR_FIRE" | "HR_ADJUST_SALARIES" | "SET_MARKETING_BUDGET" | "BUY_INGREDIENTS" | "PRODUCE_SIMPLE_RECIPE" | "SET_MENU_PRICING"
  payload: JSON
  submittedAt: ISO-8601
  clientVersion?: string
  schemaVersion?: string
}

// Exemples de payload
// HR_ADJUST_SALARIES: { deltaPct: -10..+10 }
// SET_MARKETING_BUDGET: { monthlyBudget: number }
// BUY_INGREDIENTS: { name: string, grade: string, qtyKg: number }
// PRODUCE_SIMPLE_RECIPE: { name: string, ingredient: string, grade: string, technique: string, complexity: string, portionKg: number, portions: int }

TurnResultDTO {
  gameId: UUID
  turn: int
  restaurant: string
  clients_attribues: int
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
  losses: { lost_total, lost_stock, lost_capacity, lost_other }
  schemaVersion?: string
}
```

Correspondances code: `TurnResult` (pydantic) dans `FoodOPS_V1/core/results.py` et actions issues de l’UI « bureau du directeur ».
# 🏗️ Vue d’ensemble (diagramme blocs)

```
+------------------+           REST/JSON            +------------------+
|  Interface       |  POST /actions, GET /state     |   API Gateway    |
|  Utilisateur     | <----------------------------> |  (Stateless)     |
|  (Web/Mobile)    |     WS /events (subscribe)     |  AuthN/AuthZ     |
+------------------+                                +--------+---------+
                                                          |
                                                          | calls
                                                          v
                                                 +--------+---------+
                                                 |  Service Jeu     |
                                                 |  (Moteur)        |
                                                 |  - Validation    |
                                                 |  - Résolution    |
                                                 +--------+---------+
                                                          |
                                                          | read/write
                                                          v
                                                 +--------+---------+
                                                 | Base de Données  |
                                                 |  - actions_log   |
                                                 |  - state_snap    |
                                                 |  - games, users  |
                                                 +------------------+
                                                          ^
                                                          | publish
                                                          |
                                                WebSocket/Event Stream
```
### Concrétisation moteur FoodOPS (cycle de tour)

Le moteur concret est implémenté dans `FoodOPS_V1.core.game.Game.play()` et enchaîne des étapes déterministes par tour (1 tour = 1 mois):

1) Péremption produits finis: `inventory.cleanup_expired(tour)`
2) Reset minutes RH: `restaurant.reset_rh_minutes()`
3) Allocation de la demande: `allocate_demand(restaurants, scenario)` (segmentation + score `rules.scoring.attraction_score`)
4) Bornage par capacité: `clamp_capacity(restaurants, allocated)` avec `compute_exploitable_capacity()`
5) Limitation minutes de service: `_service_capacity_with_minutes(...)`
6) Vente FIFO: `_sell_from_finished_fifo(restaurant, qty)` calcule le CA et purge FIFO
7) Pertes & notoriété: `_apply_client_losses(...)` ajuste `restaurant.notoriety`
8) Comptabilisation: `post_sales`, `post_cogs`, `post_services_ext`, `post_payroll`, `post_depreciation`
9) Prêts: `split_interest_principal(...)` + `post_loan_payment`

Chaque tour produit un `TurnResult` par restaurant (KPI) affiché par l’UI.
# 🖥️ Interface Utilisateur (indépendante)

**Rôle**

* Afficher l’état/les tours.
* Collecter les actions (avec pré-validation légère côté client).
* S’abonner aux événements temps réel.

**Flux**

* **Lecture** : `GET /games/{id}/state`, pagination sur historique des tours.
* **Écriture** : `POST /actions` (unifié, jamais d’écriture directe sur l’état).
* **Temps réel** : `WS /events?gameId=...`.

**Structure**

* Store local (Redux/Pinia/Zustand) synchronisé aux `EventDTO`.
* Optimistic UI : afficher “en attente” jusqu’à `ACTION_ACCEPTED` / `ACTION_REJECTED`.

# 🗄️ Base de données (simple & robuste)

**Modèle hybride** : journal d’actions append-only + snapshot par tour.

```
tables:
  games(
    game_id PK, status ENUM('ACTIVE','ENDED'),
    turn INT, created_at, ended_at NULL
  )

  players(
    player_id PK, game_id FK, name, seat, created_at
  )

  actions_log(
    action_id PK, game_id FK, player_id FK,
    turn INT, type, payload JSONB,
    submitted_at TIMESTAMPTZ, UNIQUE(game_id, action_id)
  )

  state_snap(
    game_id FK, turn INT, snapshot JSONB,
    computed_at TIMESTAMPTZ, PRIMARY KEY(game_id, turn)
  )

  events_outbox(
    event_id PK, game_id FK, turn INT, kind, payload JSONB,
    published_at NULLABLE
  )
indexes:
  actions_log(game_id, turn)
  state_snap(game_id, turn)
```

**Pourquoi**

* **Rejeu** possible (recompute) si règles changent.
* **Lecture rapide** via `state_snap`.
* **Outbox** pour publier des événements **fiables** (pattern outbox).

# 🧾 Snapshot d’état par tour (FoodOPS)

Schéma JSON minimal conseillé pour `state_snap.snapshot` afin d’alimenter l’UI et rejouer:

```json
{
  "gameId": "...",
  "turn": 3,
  "scenario": { "code": "centre_ville", "population_total": 8000 },
  "restaurants": [
    {
      "name": "Resto 1",
      "type": "BISTRO",
      "funds": 125430.25,
      "notoriety": 0.57,
      "service_minutes_left": 920,
      "kitchen_minutes_left": 780,
      "inventory": { "Poulet": [["G1_FRAIS_BRUT", 2.5]], "Riz": [["G3_SURGELE", 5.0]] },
      "kpi": { "price_med": 14.5, "capacity": 960 },
      "lastTurn": {
        "clients_attribues": 540,
        "clients_serv": 520,
        "ca": 7560.0,
        "cogs": 2450.0,
        "fixed_costs": 4500.0,
        "marketing": 600.0,
        "rh_cost": 5200.0,
        "funds_start": 130000.0,
        "funds_end": 125430.25,
        "losses": { "lost_total": 20, "lost_stock": 8, "lost_capacity": 12, "lost_other": 0 }
      }
    }
  ]
}
```

# 🔐 Concurrence, sécurité, idempotence

* **Idempotence** : `actionId` unique par client --> rejoue sûr.
* **Verrou de tour** : `resolveTurn` utilise un **verrou pessimiste léger** (ou **advisory lock** Postgres) sur `(gameId, turn)`.
* **Contrôle d’accès** : JWT --> `playerId` + droits par `gameId`.
* **Fenêtre de collecte** : chronométrée par serveur (`Clock`), pas par client.


# 🧱 API (minimaliste)

```txt
POST /actions
  -> 202 Accepted | 400 ValidationError | 409 Conflict

GET /games/{id}/state
  -> GameStateDTO

GET /games/{id}/history?fromTurn=..&toTurn=..
  -> [ { turn, snapshot } ]

WS /events?gameId={id}
  -> stream EventDTO
```

### Ports/Adapters FoodOPS (persistance & événements)

Ports cibles pour le moteur (implémentations adaptables à la DB choisie):

```txt
interface StateRepository {
  appendAction(action: ActionDTO): void // idempotent (gameId, actionId)
  loadActions(gameId: UUID, turn: int): [ActionDTO]
  loadSnapshot(gameId: UUID, turn: int): GameStateDTO | null
  saveSnapshot(gameId: UUID, turn: int, snapshot: JSON): void
}

interface EventPublisher {
  publish(event: EventDTO): void // via outbox
}

table events_outbox(event_id PK, game_id, turn, kind, payload JSONB, published_at NULL)
```

Idempotence: `UNIQUE(game_id, action_id)` sur `actions_log`. Publication fiable: pattern outbox (+ job d’émission).
# 📦 Déploiement & évolutivité (sans complexifier)

* **API & Moteur** : services **stateless** (scalables horizontalement).
* **DB** : un primaire (écriture) + réplicas (lecture UI/historique).
* **Cache** : optionnel pour `/state` (clé `gameId:turn`).
* **Queue** (optionnel) : si pics, `resolveTurn` consommé par workers.

# 🧪 Testabilité

* Règles du moteur = **fonctions pures** --> tests unitaires massifs.
* **Tests de contrat** (Pact) entre API–UI et API–Moteur.
* **Tests d’intégration** : scénario multi-joueurs, timeouts, reconnexion WS.

# 🧪 Tests unitaires ciblés (FoodOPS)

- Demande/Capacité: `allocate_demand` (budget, fit, cannibalisation), `clamp_capacity` (bornage)
- Inventaire: `Inventory.sell_from_finished_fifo` (FIFO strict, CA), `cleanup_expired`
- Minutes service: `_service_capacity_with_minutes`, `consume_service_minutes`
- Financement & intérêts: `split_interest_principal`, `month_amortization`
- Scénario: `compute_segment_quantities` (arrondis)
- Compta: `Ledger.post` (équilibre D/C), `balance_sheet`
