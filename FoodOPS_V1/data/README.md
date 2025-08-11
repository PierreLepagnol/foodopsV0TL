### FoodOPS — Data

Data contains parameter tables and presets that feed the simulation. These are declarative; they define catalog prices, locals, menus, roles, and scenarios.

- **Purpose**: Provide reusable, editable inputs that shape gameplay without changing code.

- **Contents**
  - **Ingredients**: `ingredients_fr.py` (catalog and grade perception), `ingredients.py` (shim), and `ingredients_catalog.py` (multi-grade catalog used by the recipe factory).
  - **Menus**: `menus_presets_simple.py` builds menus per concept via the factory; `menus.py` is a simple legacy preset.
  - **Locals**: `locals_presets.py` (capacity, visibility, rent, fonds price); `locals.py` (alternative format).
  - **Scenarios**: `scenario_presets.py` with population and segment shares; provides `get_default_scenario()`.
  - **Roles**: `roles.py` lists market salaries and capacities per post by concept.
  - **Finance & Accounting**: `finance_params.py` (rates, durations, install costs) and `accounting_params.py` (chart of accounts, amortization years).

- **Usage**
  - Read-only at runtime; the core loop and rules consult these tables for prices, budgets, and presets.
  - Add or adjust entries to tune gameplay (e.g., segment budgets, catalog prices, rent levels).

- **Extensibility**
  - Add seasonal catalogs, new scenarios, more detailed locals, or extra segments and budgets.
  - Keep naming stable to avoid breaking lookups in rules and core.


