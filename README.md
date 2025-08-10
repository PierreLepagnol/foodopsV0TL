## FoodOPS V1 — Game Engine Overview

FoodOPS simulates operating restaurants over monthly turns. It models market demand, pricing and quality positioning, production and stock freshness, service capacity, staffing, financing, and accounting. This document describes the engine’s design and mechanics, not programming details.

### What the simulation models
- **Market demand**: population split into segments with different budgets and preferences.
- **Attraction and allocation**: demand flows to restaurants based on fit, price, quality, notoriety, and visibility, with capacity and cannibalization effects.
- **Menu and pricing**: concept-appropriate menus with techniques, complexity, ingredient grades, and suggested prices by policy.
- **Production and stock**: raw ingredients by grade and cost, finished product batches with FIFO sales and expiry.
- **Service capacity**: service speed by concept, minutes per cover, and staff minute banks limit actual service.
- **Staffing and satisfaction**: team composition and utilization impact perceived quality and future performance.
- **Finance and accounting**: opening balance, depreciation, loan servicing, and turn-to-date statements.

### Core entities (domain)
- **`Restaurant`**: concept (`FAST_FOOD`, `BISTRO`, `GASTRO`), local (capacity, visibility), menu, funds, notoriety, overheads, inventory, staff minutes and satisfaction, loan info, and a `ledger` for postings.
- **`Local`**: seats/capacity and visibility; drives demand and serves as a cap in allocation.
- **`SimpleRecipe`**: name, technique, complexity, base quality, price; may carry an ingredient grade hint for perception.
- **`Inventory`**:
  - Raw: lots with ingredient grade, unit cost, and perish tour; consumption prioritizes best grade then FIFO.
  - Finished: batches with selling price, portions, and expiry; sales strictly FIFO.
- **`Staff`**: role-based service/kitchen minutes per turn; aggregated on the restaurant to create service and production minute banks.
- **`Accounting`**: a minimal chart of accounts with standard postings for sales, COGS, services, payroll, depreciation, and loans.

### Turn lifecycle (monthly)
1. Show scenario once at the start (population, segment shares).
2. Cleanup expired inventory (raw and finished).
3. Reset staff minute banks (service/kitchen) from employees.
4. Allocate demand per segment to restaurants based on attraction and capacity.
5. Clamp by exploitable capacity (concept service speed) and by available service minutes per cover.
6. Limit by finished products in stock; sell FIFO up to the minimum of demand, capacity, minutes, and stock.
7. Compute operational result: CA from actual FIFO sales, subtract COGS recognized at production, fixed overheads, marketing, and RH cost.
8. Track client losses (stock, capacity, other) and apply a small notoriety penalty proportional to lost demand.
9. Post accounting entries: sales, COGS, services, payroll, depreciation, and loan interest/principal; update cash and outstanding balances.
10. Update RH satisfaction from utilization (minutes used vs available).
11. Display KPIs and turn-to-date income statement and balance sheet.

### Demand, attraction, and allocation
- **Attraction score** (0..1) combines:
  - **Concept-segment fit** (matrix by segment): structural alignment (e.g., fast food <==> students).
  - **Price fit**: menu median price vs segment budget and tolerance.
  - **Menu quality**: mean of recipe base qualities adjusted by concept expectations and RH satisfaction.
  - **Notoriety**: bounded 0..1, reduced when clients are lost.
  - **Visibility**: normalized from local visibility.
- **Weights** (defaults): fit 25%, price 25%, quality 25%, notoriety 15%, visibility 10%.
- **Budget filter**: restaurants with median price above a segment’s budget x tolerance are excluded for that segment.
- **Capacity exploitable**: seats x 2 services x 30 days x concept service speed.
- **Cannibalization**: more restaurants of the same type slightly reduce scores.
- **Allocation**: greedy fill per segment across ranked restaurants, respecting remaining capacity.

### Menu, pricing, and quality
- **Menu generation**: concept-appropriate items from a catalog with ingredient tiers, techniques, and complexity; quality derived from ingredient-concept fit.
- **Costing**: per-portion cost = ingredient grade cost x portion + labour/energy baseline x technique x complexity.
- **Price suggestion**: either a food-cost target by concept or a target margin per portion; stored as `price`/`selling_price` on recipes for gameplay.
- **Perception**: concept expectations adjust perceived quality by grade hints (e.g., frozen penalized in gastronomy).

### Inventory and production
- **Raw ingredients**: managed by lots with grade, unit cost, and perish tour; consumption prefers better grades and older lots (best-quality FIFO) while respecting expiry.
- **Finished products**: production adds batches with portions and expiry; sales consume batches FIFO and generate revenue at batch price.
- **COGS recognition**: recognized when produced (not when sold) and posted during the turn as `turn_cogs`.

### Capacity and staffing
- **Service speed**: per concept coefficient caps exploitable monthly capacity.
- **Minutes per cover**: concept-specific service minutes per served client; service minute bank is decremented as clients are served.
- **Staff minutes**: roles provide service and/or kitchen minutes; managers contribute lightly to both; optional satisfaction updates reflect utilization.

### Finance and accounting
- **Opening and financing**: apport, bank, and optional BPI loans establish initial cash; opening entry balances cash, equipment, loans, and equity.
- **Monthly postings**:
  - Sales (70), COGS (60), Services extérieurs (61), Payroll (64)
  - Depreciation (681/2815) based on equipment amortization
  - Loan interest (66) and principal (164) with outstanding balances updated
- **Cash update**: funds adjusted by operational result, then loan payments reduce cash.
- **Statements**: cumulative income statement and balance sheet shown per turn.

### Scenarios and segments
- **Scenarios**: predefined market contexts (e.g., student district, city center, tourist area) set total monthly population and segment shares.
- **Segments**: student, worker, family, tourist, senior; each has an average budget driving price eligibility and attraction.

### Outputs and KPIs
- Per turn and cumulatives:
  - Clients attributed vs served; losses by stock, capacity, and other
  - CA, COGS, services, marketing, payroll; funds start/end
  - Loan interest and principal; depreciation; menu median price
  - Capacity utilization, notoriety, quality mean
  - Income statement and balance sheet snapshots

### Tuning levers
- Concept service speed and minutes-per-cover
- Segment budgets and tolerance
- Scoring weights and concept-segment fit matrix
- Cannibalization factor
- Ingredient grade cost multipliers; technique/complexity factors
- Food-cost targets or per-portion margin policy
- Depreciation years; financing rates and durations

### Assumptions and limits (V1)
- 1 turn = 1 month; two services per day
- COGS recognized at production; simplified loan model; no taxes
- Demand not backlogged; remainder is lost (with notoriety impact)
- Simplified labour impact in costing (more granular RH possible later)

### Example turn narrative
- Expired lots removed; staff minutes reset
- Scenario demand split; budget-ineligible restaurants filtered
- Ranked by attraction; demand allocated with capacity and cannibalization
- Service minutes and finished stock bound actual customers served
- Revenue realized from FIFO sales; COGS and operating costs reduce funds
- Depreciation and loan payments posted; funds updated
- Client losses logged; small notoriety penalty applied
- RH satisfaction adjusted based on utilization
- KPIs and statements displayed

### Extensibility
- Add scenarios with different populations and segment mixes
- Update ingredient catalog, grades, techniques, and pricing policies
- Refine RH/production models (e.g., prep minutes by recipe, learning, absence)
- Introduce taxes, more detailed balance sheet items, or supplier terms

This document focuses solely on the simulation mechanics of FoodOPS and avoids programming or tooling specifics.