# ✅ Checklist (architecture, haut niveau)

1. **Définir le cycle de tour** (états, fenêtres d’actions, règles de résolution, conditions de fin).
2. **Spécifier les contrats** entre composants (DTO d’`Action`, `GameState`, `Event` + erreurs).
3. **Séparer les responsabilités** : Moteur (logique pure), UI (I/O), Persistance (stockage & requêtes).
4. **Choisir le flux**: append-only des actions + snapshot de l’état à chaque tour (simple & robuste).
5. **Concurrence & cohérence** : verrous/logique idempotente, horodatage, contrôle d’accès.
6. **Diffusion d’événements** : notifications en temps réel (WebSocket) + REST pour lecture/écriture.
7. **Tests & évolutivité** : logique testable (pure), services stateless, DB indexée.

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

**Validation rapide** : Contrats minimaux, extensibles via `payload`. OK.
**Amélioration** : ajouter `schemaVersion` dans chaque DTO pour les évolutions.

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

**Validation rapide** : Couplage faible, UI ↔ API ↔ Moteur ↔ DB, diffusion en push. Cohérent.
**Amélioration** : si charge élevée, séparer “lecture” (réplicas) et “écriture” (primaire).

---

# 🔄 Cycle d’un tour (séquence)

```
UI -> API: POST /actions (ActionDTO)
API -> Moteur: validate(ActionDTO)
Moteur -> DB: INSERT actions_log (idempotent on actionId)
Moteur -> WS: Event ACTION_ACCEPTED (pour tous)
[Quand condition de fin de collecte atteinte: tous ont joué OU timeout]
API/Runner -> Moteur: resolveTurn(gameId, turn)
Moteur -> DB: LOAD actions_log(turn), LOAD last snapshot
Moteur -> Moteur: compute(nextState, diffs, logs)
Moteur -> DB: INSERT state_snap(turn+1, snapshot), UPDATE games(turn)
Moteur -> WS: Event TURN_RESOLVED (diffs & résumé)
UI -> API: GET /state?gameId=... (ou reçoit le push)
```

**Validation rapide** : clair et synchrone côté écriture, asynchrone côté push. OK.
**Amélioration** : déclencher `resolveTurn` via job scheduler / message queue pour robustesse.

---

# 🧠 Moteur de jeu (logique pure)

**Rôle**

* Valider une action selon l’état courant.
* Maintenir une **fonction pure** `reduce(state, actions[]) -> nextState + events`.
* Appliquer des règles de résolution déterministes, idempotentes.

**Organisation interne**

```
/engine
  /rules
    - validators.ts       // règles d'éligibilité d'actions
    - resolvers.ts        // calcul des effets
  /core
    - reduce.ts           // applique toutes les actions du tour
    - diffs.ts            // calcule les "patches" d'état (JSON Patch)
  /services
    - repo.ts             // lecture/écriture abstraite (ports)
    - publisher.ts        // émission d'événements (port)
  /models
    - types.ts            // DTO/Domain types
```

**Ports & Adapters** (faible couplage)

* **Port `StateRepository`** : `loadSnapshot(gameId, turn)`, `appendAction(action)`, `saveSnapshot(state)`.
* **Port `EventPublisher`** : `publish(event)`.

**Validation rapide** : logique testable sans DB/UI. OK.
**Amélioration** : prévoir `Clock` abstrait pour tester les timeouts.

---

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

**Validation rapide** : UI découplée, consomme seulement REST/WS. OK.
**Amélioration** : exposer `GET /schema` pour décrire dynamiquement les types d’actions.

---

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

**Validation rapide** : cohérent, simple, infalsifiable (append-only). OK.
**Amélioration** : ajouter `checksum` d’état par tour pour audits.

---

# 🔐 Concurrence, sécurité, idempotence

* **Idempotence** : `actionId` unique par client → rejoue sûr.
* **Verrou de tour** : `resolveTurn` utilise un **verrou pessimiste léger** (ou **advisory lock** Postgres) sur `(gameId, turn)`.
* **Contrôle d’accès** : JWT → `playerId` + droits par `gameId`.
* **Fenêtre de collecte** : chronométrée par serveur (`Clock`), pas par client.

**Validation rapide** : empêche double résolution et actions concurrentes. OK.
**Amélioration** : si multi-nœuds, utiliser un **verrou distribué** (ex. Postgres advisory ou Redis Redlock).

---

# 🔁 Diagramme d’interaction détaillé

```
Participant UI
Participant API
Participant Engine
Participant DB
Participant WS

UI -> API: POST /actions {ActionDTO}
API -> Engine: validate(ActionDTO)
Engine -> DB: INSERT actions_log (on conflict do nothing)
DB --> Engine: OK | conflict
Engine -> WS: Event ACTION_ACCEPTED | ACTION_REJECTED
API --> UI: 202 Accepted

parallele:
  API/Runner -> Engine: resolveTurn(gameId, turn) [trigger: all submitted or timeout]
  Engine -> DB: SELECT actions_log(turn), SELECT state_snap(turn)
  Engine -> Engine: reduce()
  Engine -> DB: INSERT state_snap(turn+1), UPDATE games.turn
  Engine -> DB: INSERT events_outbox (TURN_RESOLVED)
  Engine -> WS: publish TURN_RESOLVED
fin
```

**Validation rapide** : respecte la séparation, push fiable. OK.
**Amélioration** : placer le trigger de `resolveTurn` dans un **job scheduler** (ex. cron/queue).

---

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

**Validation rapide** : suffisant pour jouer, relire, observer. OK.
**Amélioration** : `GET /games/{id}/diffs?turn=n` pour transmettre des deltas légers.

---

# 📦 Déploiement & évolutivité (sans complexifier)

* **API & Moteur** : services **stateless** (scalables horizontalement).
* **DB** : un primaire (écriture) + réplicas (lecture UI/historique).
* **Cache** : optionnel pour `/state` (clé `gameId:turn`).
* **Queue** (optionnel) : si pics, `resolveTurn` consommé par workers.

**Validation rapide** : reste simple par défaut, extensible si charge. OK.
**Amélioration** : métriques (latence validation, durée résolution, taille actions/turn).

---

# 🧪 Testabilité

* Règles du moteur = **fonctions pures** → tests unitaires massifs.
* **Tests de contrat** (Pact) entre API–UI et API–Moteur.
* **Tests d’intégration** : scénario multi-joueurs, timeouts, reconnexion WS.

**Validation rapide** : couverture ciblée aux zones risquées. OK.
**Amélioration** : fuzzer sur `payload` d’actions pour robustesse.

---

# 🗺️ Schémas explicatifs (ASCII)

## 1) Bloc logique « Ports & Adapters »

```
        +-------------------+
        |   Engine Core     |
        |  reduce/validate  |
        +----+----------+---+
             |          |
     Port:Repo|          |Port:Publisher
             v          v
       +-----+--+    +--+------+
       |  DB    |    |  WS/ES  |
       +--------+    +---------+
```

**Validation** : moteur dépend d’interfaces, pas d’implémentations. OK.

---

## 2) Données par tour (journal + snapshot)

```
Turn N:
  actions_log: [a1, a2, ...]
  state_snap:  snapshot(N)

Turn N+1:
  actions_log: [b1, b2, ...]
  state_snap:  snapshot(N+1) = reduce(snapshot(N), [b*])
```

**Validation** : deterministic & rejouable. OK.
**Amélioration** : stocker aussi les `diffs` JSON Patch pour optimiser réseau.

---

## 3) États & phases de partie

```
[COLLECT] --(all submitted or timeout)--> [RESOLVE] --(engine done)--> [COLLECT next]
   |                                                         |
   +----------------(win/lose conditions)------------------> [ENDED]
```

**Validation** : cycle simple, lisible. OK.

---

# 📄 Exemple de types (pseudo-code TypeScript)

```ts
type Phase = "COLLECT" | "RESOLVE" | "ENDED";

interface GameState {
  gameId: string;
  turn: number;
  phase: Phase;
  world: any;
  players: Record<string, any>; // public parts only
}

interface Action {
  actionId: string;
  gameId: string;
  playerId: string;
  turn: number;
  type: string;
  payload: any;
  submittedAt: string;
}

interface ResolutionResult {
  nextState: GameState;
  events: EventDTO[];
  diffs: any[]; // JSON Patches pour UI
}
```

**Validation** : clair, facilement sérialisable. OK.
**Amélioration** : séparer `PublicState`/`PrivateState` si informations secrètes (brouillard de guerre).

---

# 🧭 Stratégie d’évolution (faible couplage)

* **Versionner** les schémas (`schemaVersion`) et **ne jamais** casser les contrats.
* **Feature flags** côté moteur (activer de nouvelles règles par jeu).
* **Migration douce** : recalcul de snapshots via rejouage en tâche planifiée.

**Validation** : permet d’évoluer sans downtime. OK.

---

## ✅ Résumé livrable

* **Plan** clair : moteurs purs, UI indépendante, DB append-only + snapshot.
* **Contrats** précis + APIs minimales (REST/WS).
* **Diagrammes ASCII** (blocs, séquences, données).
* **Validations** après chaque section, avec propositions d’amélioration ciblées.

Si tu veux, je peux adapter ce plan à un moteur concret (ex. jeu de stratégie à points d’action) et livrer des **squelettes de code** pour l’Engine, l’API et un **schéma SQL** prêt à exécuter.
