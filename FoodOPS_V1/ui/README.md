### FoodOPS — UI (Console)

UI contains console-oriented views and interactive helpers. The engine degrades gracefully if UI modules are missing; displays are best-effort.

- **Purpose**: Present KPIs, statements, and management choices to a player/operator.

- **Modules**
  - **Views**: `results_view.py` (turn KPIs and bars), `accounting_view.py` (income statement and balance sheet), `scenario_view.py` (scenario summary), `console_style.py` (color helpers).
  - **Director office**: `director_office.py` offers simple hiring, firing, salary, marketing, pricing, and training actions.
  - **Recipes**: `director_recipes.py` and `recipe_editor.py` for building and adjusting recipes/menus with suggested pricing policies.
  - **Finance**: `finance_wizard.py` provides a small, optional assistant for financing inputs.

- **Boundaries**
  - UI reads and writes to the same domain objects the core loop uses, but contains no game mechanics; those live in `core/` and `rules/`.
  - All UI interactions are optional; the core engine can run scripted scenarios without user input.

- **Extensibility**
  - Add dashboards, multi-restaurant summaries, or alternative front-ends without touching the engine.


