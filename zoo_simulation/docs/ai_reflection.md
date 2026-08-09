# AI Reflection

## Scope of AI usage

AI assistance (Claude Code) was used throughout the project, across
all three focus areas — from implementing individual classes to
reviewing planning documents against the code and fixing gaps between
them. The assignment does not grade the amount of AI usage, only
whether the team understood, questioned, and verified what it
produced. This document reflects on that.

## What worked well

- **Splitting the group work along clear focus areas** (Database –
  Kaiss, Frontend – Alessio, Backend – Darnell) made it straightforward
  to hand AI-assisted work to the right person for review — whoever
  owned an area could tell immediately whether a suggested change
  matched their own plan for it.
- **Communication between contributors stayed traceable.** Cross-area
  decisions (e.g. adding `sell_ticket()`/`create_report(format)` to the
  shared `ZooController` contract, or later `hire_employee()`/
  `clean_enclosure()`) were written down as dated changelog entries in
  the relevant `planning_*.md` file at the point they were agreed on,
  not just discussed and forgotten. That made it possible for someone
  working on a different area weeks later to see *why* a signature
  looked the way it did, instead of guessing.

## What did not work as well

- **The planning had to be adjusted more often than expected while
  implementing.** The clearest recurring example: several methods were
  first planned to return nothing (`void`), and only turned out to need
  a return value once the calling code was actually written. This
  happened more than once at different layers:
  - Every `save*()` method in the repository interfaces was originally
    diagrammed as `void`; in practice every one of them needed to
    return the newly generated row's `int` id (the calling code has no
    other way to know it, since SQLite assigns the id on insert).
  - `ZooService.add_animal()` had the same issue one layer up — the
    Flask route needs the new animal's id to redirect to it
    (`?highlight=<id>`), which only became obvious once that route was
    actually written.

  In both cases the mismatch was caught and the diagrams were corrected
  to match the code afterwards, but it meant redoing part of the
  planning instead of getting it right the first time.

## What we would do differently next time

- **More planning up front**, specifically: before diagramming a
  method, trace through how its caller will actually use the result,
  not just what the method conceptually "does". A `save()` method
  conceptually just persists something, but the *caller's* need for the
  new id was the part that got missed.

## Human-in-the-loop: concrete examples

The assignment specifically asks for evidence that AI output was
critically checked, not just accepted. A few concrete cases from this
project, not generic statements:

- **Three crashes only found by running the code, not by reading it.**
  The repository layer's `_row_to_animal()` / `_row_to_employee()` /
  `_row_to_zoo()` methods built domain objects (`Lion`, `Administrator`,
  `Zoo`) without arguments those constructors actually require
  (`behaviors`, `finance_manager`, `enclosures`/`inventory`/
  `finance_manager`). The code looked correct on a read-through; the
  `TypeError`s only appeared once it was executed end-to-end against a
  real SQLite database. The fix (composed-repository dependency
  injection) was then verified the same way — a real round-trip
  save/get for all affected domain types — instead of trusting that the
  fix "looked right".
- **A UI bug fix was not accepted on the AI's word alone.** A reported
  "the popup won't close" bug turned out to be a CSS specificity issue
  (`.hidden` losing to `.animal-popup { display: flex }` due to load
  order). The fix was only accepted after driving the actual page in a
  real browser and confirming via screenshot that the popup was gone —
  not because the diff looked reasonable.
- **Analysis and implementation were deliberately kept as separate,
  explicitly-authorized steps** when reviewing the Database area against
  the grading rubric: first an audit-only pass ("list what's missing,
  change nothing"), reviewed by hand, and only then a separate,
  explicitly requested pass to actually implement the fixes — followed
  by a third, independent re-check pass. This kept a human decision
  point between "AI found a problem" and "AI changed code" rather than
  letting one flow automatically into the other.

## Extensibility of the program

Judging by where new functionality would plug in without changing
existing contracts:

- **New animal species**: add a subclass of `Animal` (like `Lion`,
  `Giraffe`, `Penguin`) implementing the abstract methods; the
  repository layer's discriminator-based reconstruction (`species`
  column → class lookup) and the `ZooController`'s `_SPECIES_TO_CLASS`
  dispatch table already generalize to any number of species without
  further changes elsewhere.
- **New enclosures/habitat types**: `Enclosure` is not subclassed by
  type — `enclosure_type` is a plain attribute — so adding a new
  habitat is a data change (a new seeded row), not a code change,
  though the frontend's client-side species/habitat matching
  (`static/js/game.js`) would need its lookup table extended to treat
  a new type as valid for a species.
- **New employee capabilities**: the `Employee` hierarchy
  (`Zookeeper`/`Veterinarian`/`Administrator`) already separates
  role-specific behaviour into subclasses; adding a capability to an
  existing role means adding a method there, and it only becomes
  reachable from the UI once a matching `ZooService`/`ZooController`
  method is added and wired to a route — the same three-layer pattern
  `hire_employee()`/`clean_enclosure()` followed when they were added.
