### FoodOPS — Domain

The domain defines the core business objects of the simulation
These are plain data-centric entities with minimal logic, designed for clarity, testability, and reuse across the engine.

- **Purpose**: Model restaurants, menus, ingredients, inventory, and staff as passive structures
    Avoid side effects; keep rules and orchestration elsewhere.

- **Key objects**
  - **`Restaurant`**: concept (`FAST_FOOD`, `BISTRO`, `GASTRO`), local, menu (`SimpleRecipe`), funds, notoriety, overheads, inventory, loan info, staff team, service/kitchen minute banks, RH satisfaction, and `ledger` reference.
  - **`Local`**: seats/capacity and visibility
    Drives demand and constrains service.
  - **`SimpleRecipe`**: recipe item with technique, complexity, price (`price`/`selling_price`), and base quality
    May carry a grade hint via its ingredients list.
  - **`Recipe` / `RecipeLine` / `PrepStep`**: richer recipe model (portion yields, raw/net quantities) for future expansion.
  - **Ingredients**: `IngredientCategory`, `FoodGrade`, and `Ingredient` abstractions
    Grades represent procurement tiers used by rules.
  - **`Inventory`**: raw ingredient lots (grade, unit cost, perish tour) and finished product batches (portions, expiry)
    FIFO for both consumption and sales.
  - **Staff**: `Employe`, `Role`, and role productivity minutes (service/kitchen) per turn; used to compute minute banks on `Restaurant`.
  - **Types**: `RestaurantType` enums (duplicate compatibility shims exist in `domain/types.py` and `domain/restaurant_type.py`).
  - **Legacy helpers**: `stock.py` is a simpler inventory model kept for compatibility.

- **Responsibilities and boundaries**
  - Keep domain objects simple and serialization-friendly.
  - Do not embed allocation, scoring, costing, or accounting algorithms here.
  - Provide small utility methods only where they are intrinsic (e.g., computing minutes, cloning recipe price).

- **Interactions**
  - Used by the core loop to run turns and mutate state (inventory, funds, minutes, ledger reference).
  - Consumed by rules for scoring, costing, labour calculations, and recipe/menu generation.
  - Populated from data presets (locals, ingredients, menus, scenarios).

- **Extensibility**
  - Add fields with care; prefer optional attributes for forward compatibility.
  - Maintain consistent grade/category semantics across domain and data.
  - Keep calculation-heavy logic in `rules/` and orchestration in `core/`.


