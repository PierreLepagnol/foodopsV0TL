### FoodOPS — Core

Core orchestrates the simulation: market demand allocation, per-turn operations, accounting posts, and financing effects. It coordinates domain state with rules and data, and invokes UI for display.

- **Purpose**: Run the monthly turn loop and apply all systemic effects in the right order.

- **Modules**
  - **`game.py` / `turn.py`**: turn engines. Each implements the monthly lifecycle: cleanup, staff minutes, demand allocation, capacity clamping, FIFO sales from finished products, operational result, losses and notoriety, accounting posts (sales, COGS, services, payroll, depreciation, loans), funds update, and optional RH satisfaction.
  - **`market.py`**: demand allocation from scenario segments → restaurants using attraction scores, budget filters, exploitable capacity per concept, greedy redistribution, and cannibalization penalty.
  - **`accounting.py`**: minimal ledger, standard postings, income statement and balance sheet builders, and equipment amortization.
  - **`finance.py`**: simple financing plan (apport, bank, BPI), dossier fees, monthly payments, and initial cash.
  - **`setup.py`**: interactive creation of restaurants and posting of the opening balance.
  - **Other**: `game_types.py` and `results.py` are legacy/alternate result helpers.

- **Turn lifecycle (high level)**

1) Inventory cleanup
2) staff minutes reset
3) demand allocation and capacity clamp
4) stock-bound service and FIFO sales
5) operating result
6) losses + notoriety
7) accounting posts (COGS is recognized at production)
8) loan flows and funds update
9) optional RH satisfaction ==> 1
0) statements and KPIs display.

- **Interactions**
  - Consumes data (scenarios, catalogs, presets) and rules (scoring, costing, factory).
  - Mutates domain state (inventory, funds, minutes, ledger entries) deterministically.
  - Invokes UI views if present; engine remains robust without them.

- **Extensibility**
  - Swap allocation strategies, add service-minute policies per role, or refine the loss model without altering domain or rules contracts.
  - Integrate new financial instruments or taxes by extending accounting posts and statements.


