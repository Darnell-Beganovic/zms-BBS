# Test Plan

## 1. How this document fits into the project

`planning.md` (shared architecture) and the three focus-area planning
documents (`planning_db_kaiss.md`, `planning_frontend_alessio.md`,
`planning_backend_darnell.md`) describe *what* the system is and *why*
it is structured the way it is. This document describes *how it is
tested*.

Per the assignment brief, test cases are **described, not
implemented** — there is no `pytest` suite (see `README.md`'s
Technology Stack note). Instead, every method across the codebase
carries its own `Test:` docstring block with at least two Given/When/Then
cases, directly next to the code it describes, so the test case and the
implementation can never drift apart silently.

This file does **not** duplicate every one of those blocks — that would
just be a second copy to keep in sync. It is the project-level index:
the overall strategy, how much of the codebase is covered, and a
curated set of representative cases per layer, each with a pointer to
the file that holds the full, authoritative version.

Responsibility for this document is shared across the team, like the
rest of `docs/` per `README.md`'s "Architecture, integration, code
review and documentation remain shared responsibilities" note — it is
not tied to a single focus area, since it summarizes all three.

## 2. Conventions

- **Format**: `Given <preconditions>, when <action>, then <expected
  outcome>` — plain prose bullets under a `Test:` heading inside the
  method's docstring.
- **Minimum**: at least two cases per method — one "normal path" case,
  one edge/failure case — per the assignment's "für jede Funktion
  müssen mindestens 2 Tests beschrieben ... werden".
- **IDs**: the Frontend layer (`zoo_view.py`, `controller_stub.py`, and
  the `static/js/*.js` files) additionally tags each case with a stable
  ID (`TC-Vxx` for routes, `TC-Mxx` for the mock controller, `TC-Axx`/
  `TC-Gxx`/etc. for JS modules), since those files are large and the
  IDs make individual cases easy to reference from bug reports or
  commit messages. The Database and Backend layers were written later
  and use plain bullets without IDs — equally valid, just a different
  house style established independently by each contributor.
- **No shared/mocked-object framework**: since nothing here is
  executed by a test runner, cases are written against real inputs and
  real (or clearly named "double") collaborators, not a mocking
  library.

## 3. Coverage by layer

Counted directly from the current codebase (methods with a `Test:`
block vs. total `def`s in that layer):

| Layer | Files | Methods | With `Test:` | Notes |
|---|---:|---:|---:|---|
| `domain/` | 23 | 130 | 79 | Gap is almost entirely simple `@property` getters/setters (e.g. `Animal.name`, `Zoo.enclosures`) that return a stored value with no branching — not separately cased. Substantive methods (`_validate_value`, `adjust_health`, `feed`, `calculate_welfare`, …) are all covered. |
| `repositories/` | 15 | 80 | 80 | 1:1 — every repository method, including private `_row_to_*` reconstruction helpers, has cases. |
| `services/` | 4 | 17 | 17 | 1:1. |
| `controller/` | 2 | 13 | 13 | 1:1 (includes module-level helper functions like `_default_behaviors`, not just the `ZooController` class). |
| `simulation/` | 4 | 18 | 11 | Same property-getter pattern as `domain/` (`SimulationEngine.zoo`/`.event_scheduler`/`.environment`/`.current_step`); every method that actually does something (`tick`, `update_animals`, `update_enclosures`, `process_daily_costs`, `schedule_event`, `get_due_events`, `execute_due_events`) is covered. |
| `frontend/*.py` | 4 | 23 | 24* | *Some methods carry more than one `Test:` heading (helper + route), so the count exceeds the `def` count; 71 unique `TC-`-IDs in total. |
| `frontend/static/js/*.js` | 6 | — | 43 blocks | 88 unique `TC-`-IDs; JS uses top-level `function` declarations rather than class methods, counted separately. |
| `database/` (`schema.sql` comments + connection helpers) | 2 | 12 | 12 | 1:1. |

Net: the only systematic, explainable gap is trivial property
accessors. No method containing actual logic was found without a
documented test case.

## 4. Representative test cases

A small, curated sample — not exhaustive; see the referenced file for
the complete set on any class.

### Domain (`domain/`)

- `Animal.__init__` (`domain/animals/animal.py`): *Given* an empty
  `behaviors` list, *when* the constructor is called, *then* a
  `ValueError` is raised — every `Animal` must have at least one
  `Behavior` (domain invariant, not just a type hint).
- `Animal._validate_value` (`domain/animals/animal.py`): *Given*
  `value=150`, *when* `_validate_value(150)` is called, *then* it
  returns `100` — stats are clamped to `[0, 100]` at the point of
  mutation, not just documented as "should be 0-100".
- `Animal.adjust_health` (`domain/animals/animal.py`): *Given*
  `health=90`, *when* `adjust_health(20)` is called, *then* `.health`
  is `100`, not `110` — confirms the clamp applies through the public
  mutator, not only in the raw setter.

### Database / Repositories (`repositories/`, `database/`)

- `SQLZooRepository._row_to_zoo` (`repositories/sqlite/sqlite_zoo_repository.py`):
  *Given* a `zoo` row, *when* `_row_to_zoo()` reconstructs it, *then*
  `.enclosures`, `.inventory` and `.finance_manager` are real,
  populated objects built via the composed sibling repositories — not
  empty placeholders (this was a real bug, fixed 2026-08-09, see
  `planning_db_kaiss.md` §2.1).
- `schema.sql` `CHECK` constraints: *Given* an `UPDATE` sets
  `animal.health = 101`, *when* the statement executes, *then* SQLite
  raises `IntegrityError` — range validation is enforced at the
  database level as well as in `Animal._validate_value`, so a bug that
  bypasses the domain layer (e.g. a raw SQL script) still cannot
  corrupt data.

### Backend (`services/`, `controller/`, `simulation/`)

- `ZooService.feed_animal` (`services/zoo_service.py`): *Given* an
  `animal_id` that does not exist in the managed zoo, *when*
  `feed_animal()` is called, *then* it raises rather than silently
  doing nothing — callers (the controller) are required to translate
  that into a Result-dict failure, not swallow it.
- `SimulationEngine.tick` (`simulation/simulation_engine.py`): *Given*
  a zoo with 2 enclosures and 3 animals, *when* `tick()` is called
  once, *then* every animal's `hunger`/`energy`/`age` is updated
  exactly once and `current_step` increases by 1 — confirms the
  orchestration order (clock → animals → enclosures → costs → events)
  actually runs end to end, not just that each sub-step exists.
- `ZooController.add_animal` (`controller/zoo_controller.py`): *Given*
  `enclosure_id` refers to an enclosure that is already at capacity,
  *when* `add_animal()` is called, *then* the Result-dict has
  `success=False` with a descriptive message and no `Animal` is
  persisted — mirrors `Enclosure.has_capacity()` in the domain model,
  so the same rule is enforced whether an animal is added via seeding,
  the domain API, or the web form.

### Frontend (`frontend/`)

- `TC-V03`/`TC-V04` (`frontend/zoo_view.py`, `index()`): *Given*
  `ZooController.show_status()` returns `success=False`, *when* the
  dashboard route handles that response, *then* a flash error is shown
  instead of a raw exception page.
- `TC-M01`/`TC-M02` (`frontend/controller_stub.py`): *Given* two
  independent `MockZooController` instances, *when* one is mutated
  (e.g. `feed_animal()`), *then* the other is unaffected — no shared
  module-level state between instances.
- `TC-A05` (`frontend/static/js/animation.js`, `moveSprite`): *Given* a
  sprite near the right edge of its 260px enclosure box, *when*
  `moveSprite()` is called repeatedly, *then* `sprite.style.left` never
  exceeds the box width minus the sprite width — pure client-side
  bounds check, no server round-trip.

## 5. Edge cases & boundary conditions explicitly covered

- Stat clamping at both boundaries (0 and 100), not just "too high".
- `CHECK` constraint boundaries: 0 and 100 are accepted, -1 and 101 are
  rejected, on both `INSERT` and `UPDATE`.
- Enclosure at exactly full capacity (not just "over capacity").
- Feeding/adopting into a non-existent or mismatched enclosure.
- Empty `behaviors` list on `Animal` construction (rejected, not
  defaulted).
- Two independent instances of the same stub/service never sharing
  state.
- Missing/malformed form input on every POST route (empty name, `-1`
  price, non-integer IDs) — rejected with a 400/flash message before
  any controller call, not passed through.

## 6. Known, deliberately untested limitations

These are documented design trade-offs (see the relevant planning
doc's changelog section), not bugs — listed here so it is clear they
were a conscious decision, not an oversight:

- `Zoo.save()` does not cascade-persist composed `Enclosure`/
  `Inventory` objects — saving a `Zoo` only writes the `zoo` row itself
  (`planning_db_kaiss.md`, "`save()` non-cascading" entry).
- `Behavior` objects are not persisted; a reconstructed `Animal` always
  gets a fresh default `Behavior` set rather than its original one
  (`planning_db_kaiss.md`, "Behavior non-persistence" entry).
- `FinanceManager` has no database identity of its own; every
  reconstruction creates a new instance from the current balance
  (`planning_db_kaiss.md`, "FinanceManager non-identity" entry).
- Repository reconstruction assumes a single zoo per database
  (`planning_db_kaiss.md`, "single-zoo scoping" entry).

## 7. Out of scope

- No automated test runner (`pytest` or otherwise) — by design, per
  the assignment brief.
- No load/performance testing.
- No cross-browser testing beyond the primary development browser.
- No authentication/authorization testing — the project has no
  authentication layer (see `planning.md`'s explicitly out-of-scope
  items).
