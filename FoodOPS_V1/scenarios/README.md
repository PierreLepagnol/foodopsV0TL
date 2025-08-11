### FoodOPS — Scenarios

Scenarios package example scenario objects for the engine. These are lightweight descriptors used by the core loop to set the number of turns and market demand context.

- **Purpose**: Provide ready-to-use contexts (length of play and demand shape) to run the simulation.

- **Contents**
  - **`default.py`**: `DefaultScenario` with fields like `nb_tours` and `demand_per_tour` (legacy/simple path).
  - Primary scenarios are defined in `data/scenario_presets.py` and exposed via `get_default_scenario()`.

- **Usage**
  - The core loop selects a default scenario if available and prints its population and segment mix.

- **Extensibility**
  - Create new scenario modules here or expand the presets in `data/` to vary population totals and segment distributions.


