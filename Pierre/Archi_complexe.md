# ✅ Checklist (3–7 étapes clés)

1. **Définir le modèle de domaine** : `Game`, `Player`, `Turn`, `Action`, `State`, `RuleSet`, `Event`.
2. **Isoler le moteur de jeu** (pur & déterministe) : interfaces d’actions/états, règles, validation, simulation.
3. **Concevoir l’I/O** via une **API stateless** et des **events** (WebSocket/SSE) pour diffuser états/résultats.
4. **Choisir un stockage** orienté **Event Sourcing + snapshots** + vues matérialisées (CQRS).
5. **Mettre en place un orchestrateur de tours** (queue/job par partie, verrouillage, timeout).
6. **Standardiser les contrats** (JSON schémas versionnés) pour **actions** & **états** envoyables à tout client.
7. **Planifier l’évolutivité** : partitionnement par partie, scaling indépendant UI / moteur / DB.

---

# 🧱 Architecture globale (découplée)

```
+--------------------+       HTTPS/gRPC        +---------------------+
|   UI Clients       |  <--------------------> |  API Gateway / BFF  |
| (Web/Mobile/CLI)   |   REST(Action POST)     |  (Auth, Rate-limit) |
| WS/SSE pour updates|   WS/SSE(State/Event)   +----------+----------+
+---------+----------+                                 |
          |                                             | Commands/Queries
          |                                             v
          |                                    +--------+---------+
          |                                    |  Game App Svc    |
          |  Publish State/Event               | (CQRS Facade)    |
          |<-----------------------------------+ (Validation thin)|
          |                                    +----+--------+----+
          |                                         |        |
          |                      Commands (enqueue) |        | Queries (read models)
          |                                         v        v
          |                                     +---+--------+----+
          |                                     | Turn Orchestrator|
          |                                     | (Workers/Queues) |
          |                                     +---+--------+----+
          |                                         |        |
          |      Deterministic calls                |        |
          |                                         v        |
          |                                   +-----+-----+  |
          |                                   |  Game     |  |
          |                                   |  Engine   |  |
          |                                   +-----+-----+  |
          |                                         |        |
          |                    Domain Events        |        |
          |                                         v        v
          |                                  +------+--------+------+
          |                                  |   Event Store        |
          |                                  | + Snapshots +        |
          |                                  |   Read Models (DB)   |
          |                                  +------+--------+------+
          |                                         |
          |                         Project to WS/SSE topics
          v                                         v
+---------+----------+                       +------+--------+
|   UI Clients       | <---------------------|  Realtime Hub |
+--------------------+     state/events      +---------------+
```

**Validation rapide** : la séparation UI / Orchestrateur / Moteur / DB est nette, flux unidirectionnels pour les commandes et projections pour la lecture → **cohérent**. Si la latence d’update doit être ultra-basse, envisager un **cache in-memory** côté Realtime Hub.

---

## 1) Moteur de jeu (core déterministe)

### Rôle

* Valider & appliquer des **Actions** sur un **State** via un **RuleSet**.
* Produire des **DomainEvents** (ex. `ActionApplied`, `TurnAdvanced`, `DamageDealt`).
* Être **pure function** autant que possible : `nextState = engine.apply(state, actions, seed)` → testable, rejouable.

### Interfaces (pseudo-code)

```ts
// Types versionnés
type Versioned<T> = T & { schemaVersion: string };

interface Action extends Versioned<{}> {
  gameId: string; turn: number; playerId: string; type: string; payload: any;
}

interface GameState extends Versioned<{}> {
  gameId: string; turn: number; players: PlayerState[]; map: MapState; meta: {};
}

interface RuleSet {
  id: string;
  validate(state: GameState, action: Action): ValidationResult;
  applyTurn(state: GameState, actions: Action[], seed?: number): { next: GameState; events: DomainEvent[] };
}
```

### Propriétés

* **Déterminisme** (même entrée → même sortie). RNG via **seed** stocké dans l’EventStore.
* **Idempotence** : rejeter les actions dupliquées (clé `actionId`).
* **Isolation** : aucune I/O réseau/DB dans le moteur.

**Validation rapide** : le moteur ne connaît ni la DB ni l’API → **faible couplage OK**. Attention à la stabilité des schémas → **versionner** strictement (`schemaVersion`).

---

## 2) Interface utilisateur (I/O indépendante)

### Rôle

* Soumettre des actions (`POST /games/{id}/actions`).
* S’abonner aux mises à jour (`WS /games/{id}/stream` ou SSE).
* Récupérer des états/vues (`GET /games/{id}`, `GET /games/{id}/timeline`).

### Contrats JSON (extraits)

**Action (envoyable par n’importe quel client)**

```json
{
  "schemaVersion": "action-1.0",
  "actionId": "uuid",
  "gameId": "g-123",
  "turn": 7,
  "playerId": "p-42",
  "type": "MOVE",
  "payload": { "unitId": "u-3", "to": [4,2] }
}
```

**State (diffusé à tous)**

```json
{
  "schemaVersion": "state-1.0",
  "gameId": "g-123",
  "turn": 7,
  "visibleTo": "all",
  "players": [/* redacted per fog-of-war if needed */],
  "map": { /* ... */ },
  "meta": { "deadline": "2025-08-15T20:00:00Z" }
}
```

**Validation rapide** : états/actions **autoportants & transportables** → répond à la contrainte “envoyables à n’importe quel joueur”. Si brouillard de guerre, prévoir **redaction layer**.

---

## 3) Base de données (stockage des parties)

### Choix & schéma

* **Event Store** (append-only) : `Events(gameId, seq, type, payload, timestamp, actor, turn, seed)`
* **Snapshots** périodiques : `Snapshots(gameId, turn, stateBlob, lastSeq)`
* **Read Models** (CQRS) : tables indexées pour UI (ex. `Games`, `Players`, `Leaderboards`, `GameStatePublic`)

```
Event Store (append-only)
 ├─ g-123 #1 GameCreated
 ├─ g-123 #2 PlayerJoined(p-42)
 ├─ g-123 #3 ActionQueued(actionId=...)
 └─ g-123 #4 TurnResolved(turn=7, seed=...)

Snapshots
 └─ g-123 @turn=7 (stateBlob, lastSeq=4)

Read Models
 ├─ GameSummary(g-123, status, players, turn)
 └─ GameStatePublic(g-123, turn, redactedState)
```

**Validation rapide** : Event Sourcing + snapshots permet **rejeu** & **debug**. Correction possible : ajuster la **fréquence de snapshot** selon la taille d’état (p.ex. tous les N tours).

---

# 🔁 Orchestration des tours

### Composant : Turn Orchestrator

* Consomme les actions **validées** d’un tour, applique `RuleSet.applyTurn`, émet `TurnResolved`.
* Gère **timer de tour** (deadline), **verrou par partie** (une résolution à la fois), **retry/idempotence**.
* Implémentation : **workers** tirant des **queues** partitionnées par `gameId`.

```
+-----------------+        enqueue        +---------------------+
| API/App Service | --------------------> |  Queue per GameId   |
+--------+--------+                       +----------+----------+
         |                                           |
         v                                           v
   Validate/Emit                           Turn Orchestrator (worker)
   ActionQueued                                 |
                                                 v
                                          Game Engine.applyTurn
                                                 |
                                                 v
                                           Persist events
                                                 |
                                                 v
                                           Project to reads
                                                 |
                                                 v
                                             Realtime Hub
```

**Validation rapide** : un seul worker par partie garantit l’ordre → **consistance**. Si volume élevé, utiliser **sharding** (hash(gameId) → partition).

---

# 🔌 Interactions détaillées (séquences)

### 1) Soumission d’action (happy path)

```
Client -> API: POST /games/{id}/actions {Action}
API -> AppSvc: validate(auth, schema, turn window)
AppSvc -> EventStore: append ActionQueued(actionId, payload)
AppSvc -> Queue[gameId]: enqueue(actionId)

[Plus tard / fin de tour]
Orchestrator -> EventStore: load state (replay or snapshot)
Orchestrator -> Engine: applyTurn(state, actions[turn], seed)
Engine -> Orchestrator: {nextState, events}
Orchestrator -> EventStore: append TurnResolved + derived events
Projector -> ReadModels: update GameStatePublic
RealtimeHub -> Clients: broadcast {stateDiff, events}
```

**Validation rapide** : la lecture n’attend pas la résolution → UI peut montrer **état “en attente”**. Penser à **optimistic concurrency** sur `turn`.

### 2) Rejoint / spectateur

```
Client -> API: GET /games/{id}
API -> ReadModels: fetch GameStatePublic
API -> Client: return state + stream URL
Client -> WS: subscribe /games/{id}
RealtimeHub -> Client: push future events
```

**Validation rapide** : spectateur reçoit **mêmes flux** que joueurs (états publics) → **contrainte de diffusion OK**.

---

# 🧩 Détails d’implémentation par composant

## API Gateway / BFF

* **Auth** (JWT/OAuth), **rate limiting**, **schema validation** (JSON Schema), **idempotency-key** via `actionId`.
* **Endpoints** :

  * `POST /games` (create), `POST /games/{id}/join`
  * `POST /games/{id}/actions`
  * `GET /games/{id}`, `GET /games/{id}/timeline`, `GET /games/{id}/players`
  * `WS /games/{id}/stream` (ou SSE)

**Validation rapide** : BFF stateless, ne tient pas d’état en mémoire → **scalable horizontalement**.

## Game App Service (CQRS façade)

* **Command side** : vérifie fenêtre de tour, droit du joueur, enrichit l’événement (timestamp, actor).
* **Query side** : sert des **vues matérialisées** (faible latence).

**Validation rapide** : fine couche “maigre”, logique lourde reste dans le moteur → **couplage faible**.

## Turn Orchestrator

* **Timers** (cron/Delayed queue) pour auto-clôturer un tour.
* **Verrou** par `gameId` (advisory lock/lease).
* **Observabilité** : métriques par tour (ms, nb actions, erreurs).

**Validation rapide** : verrou au niveau partie évite les races. Prévoir **dead-letter queue** pour actions invalides.

## Game Engine

* **Modules** : `validators/`, `resolvers/`, `effects/`, `rng/`.
* **Tests** : propriété de **déterminisme** (rejeu intégral d’un match → même fin).

**Validation rapide** : pas d’I/O → test & fuzz faciles. Ajouter **golden tests** (snapshots de state).

## Base de données

* **EventStore** : Postgres (table append-only) ou spécialisé (EventStoreDB). Index (`gameId, seq`).
* **Read Models** : Postgres/Elastic/Redis selon cas d’usage.
* **Snapshots** : compression (zstd), versionnage.

**Validation rapide** : séparation écriture/lecture via CQRS → **perf** et **évolution** indépendantes.

## Realtime Hub

* **Pub/Sub** interne (NATS/Redis) → topics `game.{id}`.
* **Fan-out** WS/SSE, reprise via **lastEventId**.

**Validation rapide** : hub peut scaler seul. Si >100k connexions, utiliser **sharded hubs**.

---

# 🗺️ Schémas explicatifs

## Diagramme de blocs (vue logique)

```
[UI] --REST/WS--> [API/BFF] --cmd--> [AppSvc] --enqueue--> [Queue]
                                         ^                     |
                                         |                    (per game partition)
                                       query                   v
                                         |                [Orchestrator] --calls--> [Engine]
                                         v                                      |
                                      [Read Models] <---Projector--- [Event Store + Snapshots]
                                             ^                                   |
                                             +---------- Pub/Sub ---------------+
                                                            |
                                                          [Realtime Hub] --WS--> [UI]
```

**Validation rapide** : flux lecture/écriture séparés (CQRS) → **OK**. Correction : bien **documenter idempotence** côté API.

## Diagramme séquence “Fin de tour automatique”

```
Timer -> Orchestrator: deadline reached(g-123, turn=7)
Orchestrator -> EventStore: load actions for turn=7
Orchestrator -> Engine: applyTurn(...)
Engine -> Orchestrator: nextState, events
Orchestrator -> EventStore: append TurnResolved
Projector -> ReadModels: update
Realtime -> Clients: broadcast
```

**Validation rapide** : aucun appel UI bloquant → **résilience**. Ajouter **replay** en cas de crash post-append/pré-broadcast.

## Modèle de données minimal (DDL esquisse)

```
Events(game_id, seq BIGINT PK, type TEXT, payload JSONB, turn INT, actor TEXT, seed BIGINT, ts TIMESTAMPTZ)
Snapshots(game_id, turn INT, last_seq BIGINT, state BYTEA, ts TIMESTAMPTZ)
GameStatePublic(game_id PK, turn INT, state_public JSONB, ts TIMESTAMPTZ)
```

**Validation rapide** : clés pour lecture rapide par `game_id, turn`. Ajouter index `turn` pour timeline.

---

# 🔐 Considérations transverses

* **Versionnage** : `schemaVersion` dans **Action/State/Events**. Règles de **compat ascendante** côté lecture.
* **Sécurité** : ACL par partie (membres/observateurs), filtrage des champs privés.
* **Concurrence** : **optimistic concurrency** sur `turn` (évite double clôture).
* **Observabilité** : tracing distribué (span: API → Orchestrator → Engine → DB), métriques clés.
* **Résilience** : retries exponentiels, DLQ, **exactly-once** via outbox pattern pour projections.
* **Performance** : batching d’actions, snapshots réguliers, projection asynchrone.
* **Tests** : tests de propriété (QuickCheck-style), jeux de seeds, replay intégral.

**Validation rapide** : couvre fiabilité et évolutivité. Correction : documenter un **process de migration** des schémas (migrateurs de projections & replayers).

---

# 🛠️ Plan de mise en œuvre (étapes concrètes)

1. **Domain & Engine (v0)** : définir `Action`, `State`, `RuleSet`; implémenter `applyTurn`; tests de déterminisme.
2. **Event Store + Snapshots** : tables & repository; utilitaire de **replay** d’une partie.
3. **API/BFF minimal** : `POST /actions`, `GET /games/{id}`, `WS /stream`.
4. **Turn Orchestrator** : worker + queue; timers; verrouillage par `gameId`.
5. **Projections** : `GameStatePublic`, timeline, leaderboards.
6. **Realtime Hub** : diffusion WS/SSE; résilience (lastEventId).
7. **Hardening** : auth, idempotency, rate limiting, observabilité.

**Validation rapide** : ordre permet de jouer vite (vertical slice) et d’itérer. Correction : prévoir un **simulateur de charge** (bots) avant prod.

---

# 📦 Exemple de contrats (JSON Schema, abrégé)

```json
// action-1.0.schema.json
{
  "$id": "action-1.0",
  "type": "object",
  "required": ["schemaVersion","actionId","gameId","turn","playerId","type","payload"],
  "properties": {
    "schemaVersion": { "const": "action-1.0" },
    "actionId": { "type": "string", "format": "uuid" },
    "gameId": { "type": "string" },
    "turn": { "type": "integer", "minimum": 0 },
    "playerId": { "type": "string" },
    "type": { "type": "string" },
    "payload": { "type": "object" }
  }
}
```

```json
// state-1.0.schema.json
{
  "$id": "state-1.0",
  "type": "object",
  "required": ["schemaVersion","gameId","turn"],
  "properties": {
    "schemaVersion": { "const": "state-1.0" },
    "gameId": { "type": "string" },
    "turn": { "type": "integer" },
    "visibleTo": { "type": "string", "enum": ["all","player","spectator"] },
    "map": { "type": "object" },
    "players": { "type": "array" },
    "meta": { "type": "object" }
  }
}
```

**Validation rapide** : schémas **clairs** & versionnés → favorisent l’évolution indépendante des clients.

---

# 🧪 Pseudo-code d’un tour

```ts
function resolveTurn(gameId: string, turn: number) {
  const { state, lastSeq } = loadSnapshotOrReplay(gameId);
  const actions = loadQueuedActions(gameId, turn).sort(bySubmissionTime);
  // 1) Validation
  for (const a of actions) {
    assertVersion(a.schemaVersion, "action-1.0");
    rules.validate(state, a).throwIfInvalid();
  }
  // 2) Seed (determinisme)
  const seed = prngSeedFrom(lastSeq, gameId, turn);
  // 3) Résolution
  const { next, events } = rules.applyTurn(state, actions, seed);
  // 4) Persistance atomique
  appendEvents(gameId, [
    ...events,
    { type: "TurnResolved", turn, seed }
  ]);
  // 5) Snapshot (optionnel)
  if (shouldSnapshot(turn)) saveSnapshot(gameId, turn, next);
  // 6) Projection + broadcast
  projectAndBroadcast(gameId, next, events);
}
```

**Validation rapide** : toutes les sorties dérivent d’entrées persistées (actions + seed) → **reproductibilité garantie**.

---

# 🧯 Points d’attention & améliorations immédiates

* **Actions tardives** : définir un statut `LateActionRejected` et notifier l’expéditeur.
* **Actions conflictuelles** : verrou par unité/ressource pendant la soumission (optionnel) ou résolution pessimiste dans le moteur.
* **Fog-of-war** : générer **états personnalisés** par joueur (projo par joueur) si nécessaire.
* **Modding/Rulesets** : charger un `RuleSet` par `gameId` (plugins versionnés).

**Validation rapide** : ces options n’augmentent pas le couplage — elles se branchent via projections/règles.

---

## ✅ Conclusion

Cette architecture sépare clairement **moteur**, **I/O**, et **stockage** tout en garantissant :

* **Diffusion d’états/actions** à n’importe quel client,
* **Faible couplage** (CQRS, événements, moteur pur),
* **Évolutivité indépendante** de chaque composant.

Si tu veux, je peux transformer ce plan en **squelettes de services** (API/worker/engine) dans le langage de ton choix.
