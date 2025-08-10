### FoodOPS — Rules

Rules implement the game’s algorithms: demand scoring, costing and price policies, labour time, and procedural menu generation. They are stateless and operate on domain/data inputs to produce decisions or derived values.

- **Purpose**: Encapsulate tunable, testable game logic separate from data and orchestration.

- **Modules**
  - **`scoring.py`**: attraction score combining concept–segment fit, price fit (vs budget), menu quality, notoriety, and visibility; includes menu median price and quality estimation (with concept expectation adjustments). Weights are configurable.
  - **`costing.py`**: per-portion COGS (ingredient grade multipliers + technique/complexity labour/energy) and suggested price policies (food-cost targets per concept or margin per portion).
  - **`labour.py`**: preparation minutes per portion by technique and complexity.
  - **`recipe_factory.py`**: builds concept-appropriate menus from the ingredient catalog, selecting grades, techniques, simple items and combos, pricing, and quality hints.
  - **`recipes_factory.py`**: thin export of the factory helpers.

- **Inputs / Outputs**
  - Inputs: domain objects (restaurants, recipes), data tables (catalog, budgets), and scenario/segment info.
  - Outputs: scores, suggested prices, per-portion costs, prep minutes, and generated menus.

- **Tuning levers**
  - Scoring weights and concept–segment fit matrix.
  - Budget tolerance and price-fit shape.
  - Ingredient grade cost multipliers; technique/complexity labour multipliers.
  - Pricing policies and targets/margins.
  - Menu generation parameters (targets, combos, allowed category pairs).

- **Boundaries**
  - Market demand allocation resides in `core/market.py` (uses scoring but lives in core).
  - Domain objects remain passive; rules do not mutate persistent state.

- **Extensibility**
  - Add new pricing policies, quality models, or scoring dimensions without touching the core loop.
  - Extend the factory to support seasonal items, limited-time offers, or dietary tags.


