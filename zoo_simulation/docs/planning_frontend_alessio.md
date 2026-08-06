# Individual Planning — Frontend (Alessio Bellamacina)

This document contains the individual, schwerpunkt-specific planning for the
Frontend focus area, as required by the module assignment. Shared decisions
(overall scope, architecture, team structure) are documented in
[`planning.md`](planning.md); this document goes into the detail owned by the
Frontend role: the Flask-based web user interface.

## 1. Scope of the Frontend Focus

The Frontend focus area covers the Presentation Layer of the layered
architecture (see `planning.md` section 7.1):

- Flask routes/blueprints that expose the application's use cases
  (zoo status, feeding, treatment, finances, reports) to the browser.
- Jinja2 templates that render the data provided by the Controller layer.
- Client-facing input forms (e.g. "feed animal" form, "buy ticket" form)
  and their surface-level validation (required fields, correct types).
- Display of success/error messages returned by `ZooController`.

The Frontend never talks to the domain model, services or repositories
directly — it only calls `ZooController`, which keeps the presentation layer
replaceable (e.g. swapping Flask for another web framework later) without
touching backend logic.

## 2. Class Diagram (Frontend Focus)

Frontend-relevant subset of the full class diagram in
[`../../Projektplanung/Klassendiagramm_Code.md`](../../Projektplanung/Klassendiagramm_Code.md).
`ZooView` is realised as a set of Flask routes/templates rather than a single
console class.

```mermaid
classDiagram
    direction TB

    class ZooView {
        <<Flask blueprint>>
        +show_zoo_status(data: DataFrame) Response
        +show_animals(data: DataFrame) Response
        +show_financial_report(data: DataFrame) Response
        +show_message(message: str) Response
        +handle_feed_animal_form(request: Request) Response
        +handle_buy_ticket_form(request: Request) Response
    }

    class ZooController {
        -ZooService zoo_service
        -SimulationService simulation_service
        -ReportService report_service
        +show_status() dict
        +add_animal(data: dict) dict
        +feed_animal(animal_id: int, food_id: int) dict
        +sell_ticket(price: float) dict
        +run_simulation_step() dict
        +create_report(format: str) dict
    }

    ZooView --> ZooController : user actions (HTTP requests)
```

### 2.1 ZooController Result Contract (agreed 2026-08-06)

The class diagram in `planning.md`/`Klassendiagramm_Code.md` originally showed
every `ZooController` method returning `void`. In practice the Frontend needs
both the requested data and a success/error signal, so all `ZooController`
methods return a uniform result dict instead:

```python
{"success": bool, "message": str, "data": Any}
```

- `success` drives whether the view renders a success or error flash message.
- `message` is a human-readable string shown to the user as-is.
- `data` carries the payload the route needs to render (e.g. a DataFrame /
  dict for `show_status()`, or file info for `create_report()`).

`ZooController.sell_ticket(price: float)` was added to close a gap between
this route table and the class diagram, which had no ticket-related method
(only `ZooService.sell_ticket()` existed). `create_report()` now takes a
`format: str` argument (`"csv"`, `"xlsx"`, or `None`/`"html"` for the plain
report view) and its `data` field carries `{"file_path": str, "mimetype":
str}` so the Flask route can stream the file back with `send_file()` without
building CSV/Excel content itself.

### 2.2 Implementation Note: `Response` Return Type (agreed 2026-08-06)

The class diagram types every `ZooView` rendering/handling method (
`show_zoo_status`, `show_animals`, `show_financial_report`, `show_message`,
`handle_feed_animal_form`, `handle_buy_ticket_form`) as returning `Response`.
In the actual Flask code these functions are implemented with a Python
return type of `str` (the string produced by `render_template()`), not an
explicit `flask.Response` object. This is intentional and does not
contradict the diagram: Flask automatically wraps a `str` returned from a
view function into a full `Response` object (status 200, headers, etc.)
before it reaches the client, which is idiomatic Flask and avoids
unnecessary boilerplate (`make_response(render_template(...))`) on every
route. The diagram's `Response` return type describes the HTTP-level
outcome the client receives, not the literal Python return type of the
implementing function.

Flask route functions that only dispatch to a `ZooController` call and then
delegate rendering (e.g. the `/`-route function that calls
`ZooController.show_status()` and hands the result to `show_zoo_status()`)
are pure routing/error-handling glue and are intentionally not listed as
separate `ZooView` methods in the class diagram — only the methods that do
meaningful rendering/handling work are modelled there, per the Single
Responsibility principle already stated in section 4.

## 3. Page / Route Overview

| Route | Method | Purpose | Controller call |
|-------|--------|---------|------------------|
| `/` | GET | Show zoo dashboard (visitors, enclosures) | `ZooController.show_status()` |
| `/animals` | GET | List all animals with state (hunger, health, energy) | `ZooController.show_status()` |
| `/animals/<id>/feed` | POST | Submit feeding form | `ZooController.feed_animal(animal_id, food_id)` |
| `/tickets/buy` | POST | Submit ticket purchase form | `ZooController.sell_ticket(price)` |
| `/simulation/step` | POST | Trigger one simulation tick | `ZooController.run_simulation_step()` |
| `/reports/financial` | GET | Display / download financial report (CSV/Excel) | `ZooController.create_report(format)` |

## 4. OOP Principles Applied in the Frontend

- **Abstraction**: The Frontend only knows the `ZooController` interface, not
  the concrete domain classes behind it — the controller abstracts away
  service and repository details.
- **Single Responsibility**: Each Flask route has exactly one job (render a
  page or handle one form submission); no business logic lives in the
  view functions.
- **Separation of Concerns / MVC-inspired structure**: Presentation
  (Flask templates), application flow (`ZooController`) and business logic
  (`ZooService`) remain in distinct modules/files, matching the assignment's
  requirement for a visibly separated architecture.

## 5. Test Descriptions (described, not implemented)

Per the assignment, at least two test cases are described for each function
below; they are **not** implemented as automated pytest code.

### `handle_feed_animal_form(request)`

- TC-F01: Given a POST request with a valid `animal_id` and `food_id`, when
  the form is submitted, then `ZooController.feed_animal()` is called with
  the parsed values and a success message is rendered.
- TC-F02: Given a POST request missing the `food_id` field, when the form is
  submitted, then the request is rejected with a 400 response and an error
  message is shown, without calling the controller.

### `show_zoo_status(data)`

- TC-F03: Given a non-empty `DataFrame` of enclosures/animals, when
  `show_zoo_status` is called, then the dashboard template renders one row
  per enclosure.
- TC-F04: Given an empty `DataFrame` (no enclosures yet), when
  `show_zoo_status` is called, then a friendly "no enclosures yet" message is
  rendered instead of an empty table.

### `handle_buy_ticket_form(request)`

- TC-F05: Given a POST request with a valid ticket price, when the form is
  submitted, then `ZooController` records the sale and a confirmation page is
  rendered.
- TC-F06: Given the zoo is at `maximum_visitors` capacity, when the form is
  submitted, then an error message "zoo is full" is rendered and no
  transaction is recorded.

### `show_financial_report(data)`

- TC-F07: Given financial data exists, when the report route is requested
  with `format=csv`, then a downloadable CSV file is returned.
- TC-F08: Given financial data exists, when the report route is requested
  with `format=xlsx`, then a downloadable Excel file is returned.

## 6. Open Questions / Assumptions

- User authentication and role-based access are explicitly out of scope for
  this project (see `planning.md` section 4.2); all routes are
  unauthenticated by design, not as a temporary simplification.
- As of 2026-08-06, `ZooController` (Backend focus, Darnell) is not yet
  implemented (`controller/zoo_controller.py` is an empty file). The Frontend
  is built against `zoo_simulation/frontend/controller_stub.py`, a
  `MockZooController` that implements the exact result-dict contract from
  section 2.1 with in-memory fake data. `zoo_view.py` imports it from a
  single place so it can be swapped for the real `ZooController` import once
  it lands, without changing any route logic.
- The result-dict contract in section 2.1 (`{"success", "message", "data"}`)
  and the added `sell_ticket(price)` / `create_report(format)` signatures
  were agreed between Frontend and Backend on 2026-08-06 and should be
  reflected in `planning_backend_darnell.md`'s `ZooController` diagram once
  Darnell implements the real controller.
