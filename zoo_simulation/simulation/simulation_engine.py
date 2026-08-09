"""SimulationEngine: advances the zoo simulation by discrete time steps.

Schwerpunkt: Backend (Simulation Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.simulation.environmental_factor import EnvironmentalFactor
from zoo_simulation.simulation.event_scheduler import EventScheduler

if TYPE_CHECKING:
    from zoo_simulation.domain.zoo import Zoo

_MAX_ENVIRONMENT_ENERGY_PENALTY = 10

# Base metabolic hunger increase per tick, applied to every animal
# regardless of its composed Behaviors. Added 2026-08-09: nothing else
# in the domain model ever increased hunger (FeedingBehavior/Animal.eat()
# only ever decrease it), so animals never actually needed feeding -
# found by actually running the wired-up app. Deliberately larger than
# FeedingBehavior's passive relief (5/tick), so an animal with only
# passive foraging still gets hungrier over time and manual feeding
# stays meaningful.
_METABOLISM_HUNGER_INCREASE_PER_TICK = 12


class SimulationEngine:
    """SimulationEngine - advances the whole zoo by one discrete time step per tick.

    One `tick()` is treated as one full simulation day: it advances
    every animal's behaviors/age, decays enclosure cleanliness, deducts
    one day of employee salaries, applies the current environment's
    influence, and processes any events due at the new step - a
    deliberately simple 1-tick-equals-1-day model, since aufgabe.md
    specifies no calendar granularity.

    Known limitation (accepted 2026-08-09 while wiring the application
    entry point): purely in-memory. It mutates the composed `Zoo`
    object's Animal/Enclosure/FinanceManager state directly, but never
    persists any of that back through a repository - `Employee`
    salary deductions never become a stored Transaction, and
    hunger/energy/age/cleanliness changes never reach the database.
    Consistency with `ZooService` in the same process is still given
    (`ZooService.get_zoo()` caches and returns this exact same `Zoo`
    instance, see that class's docstring), but a process restart loses
    every effect a `tick()` ever produced. Fixing this would mean
    giving either this class or `SimulationService` repository access
    to write back changed Animals/Enclosures/Transactions after each
    tick - deliberately out of scope for now (aufgabe.md's own
    disclaimer: not meant to be a fully production-ready product).

        - Constructor: stores all attributes privately; `current_step`
          only changes through `tick()`, never assigned directly.
        - _zoo (Zoo): the zoo this engine advances. Not persisted or
          reloaded by this class - the caller (SimulationService) owns
          the Zoo instance's lifecycle.
        - _event_scheduler (EventScheduler): time-triggered events,
          checked once per tick.
        - _environment (EnvironmentalFactor): current conditions. A
          fixed snapshot for this engine's lifetime - replacing it with
          a new one each tick (e.g. changing weather) is left to a
          future caller, not done automatically here.
        - _current_step (int): the simulation clock, starts at 0.
    """

    def __init__(
        self,
        zoo: Zoo,
        event_scheduler: EventScheduler | None = None,
        environment: EnvironmentalFactor | None = None,
        current_step: int = 0,
    ) -> None:
        """Create a SimulationEngine for the given zoo.

        Args:
            zoo (Zoo): the zoo to advance.
            event_scheduler (EventScheduler | None, optional): defaults
                to a fresh, empty `EventScheduler()` if not given - most
                callers do not need to schedule anything up front.
            environment (EnvironmentalFactor | None, optional): defaults
                to a fresh, neutral `EnvironmentalFactor()` (sunny,
                20 degrees, day) if not given.
            current_step (int, optional): starting simulation time.
                Defaults to 0.

        Test:
            - Given a Zoo with no arguments beyond it, when the
              constructor is called, then `.current_step` is 0 and
              `.event_scheduler`/`.environment` are non-None defaults.
            - Given an explicit EventScheduler with pre-scheduled events,
              when the constructor is called with it, then that exact
              instance is used (not replaced by a fresh one).
        """
        self._zoo = zoo
        self._event_scheduler = event_scheduler if event_scheduler is not None else EventScheduler()
        self._environment = environment if environment is not None else EnvironmentalFactor()
        self._current_step = current_step

    @property
    def zoo(self) -> Zoo:
        return self._zoo

    @property
    def event_scheduler(self) -> EventScheduler:
        return self._event_scheduler

    @property
    def environment(self) -> EnvironmentalFactor:
        return self._environment

    @property
    def current_step(self) -> int:
        return self._current_step

    def tick(self) -> None:
        """Advance the simulation by one full step.

        Order: advance the clock, update every animal, update every
        enclosure, process one day of costs, then run any events now due
        - each sub-step is also independently callable (see
        `update_animals()`/`update_enclosures()`/
        `process_daily_costs()`), `tick()` just orchestrates them once.

        Test:
            - Given a zoo with 2 enclosures and 3 animals, when `tick()`
              is called once, then every animal's `hunger`/`energy`/`age`
              is updated exactly once and `current_step` increases by 1.
            - Given a scheduled event due at the current simulation time,
              when `tick()` is called, then
              `EventScheduler.execute_due_events()` is invoked and the
              event is removed from the pending queue.
        """
        self._current_step += 1
        self.update_animals()
        self.update_enclosures()
        self.process_daily_costs()
        self._event_scheduler.execute_due_events(self._current_step)

    def update_animals(self) -> None:
        """Update every animal in every enclosure by one step.

        Runs each animal's composed Behaviors (`Animal.update()`) and
        advances its age (`Animal.grow_older()`), then applies a small
        extra energy penalty scaled by how unfavorable the current
        `environment` is (`EnvironmentalFactor.get_influence_factor()`)
        - e.g. a storm at night costs a bit more energy than a sunny day,
        on top of whatever the animal's own Behaviors already did. Also
        applies `_METABOLISM_HUNGER_INCREASE_PER_TICK` to every animal
        (added 2026-08-09 - see that constant's comment): this, not the
        Behaviors, is what actually makes feeding necessary over time.

        Test:
            - Given an enclosure housing 2 animals, when
              `update_animals()` is called, then both animals' `update()`
              and `grow_older()` were each called exactly once and both
              animals' hunger increased.
            - Given `environment` reports an influence factor of 1.0
              (fully favorable), when `update_animals()` is called, then
              no extra energy penalty is applied beyond the animals' own
              Behaviors (hunger still increases from metabolism).
        """
        penalty = round((1 - self._environment.get_influence_factor()) * _MAX_ENVIRONMENT_ENERGY_PENALTY)
        for enclosure in self._zoo.enclosures:
            for animal in enclosure.animals:
                animal.update()
                animal.grow_older()
                animal.adjust_hunger(_METABOLISM_HUNGER_INCREASE_PER_TICK)
                if penalty > 0:
                    animal.adjust_energy(-penalty)

    def update_enclosures(self) -> None:
        """Update every enclosure in the zoo by one step.

        Each enclosure's cleanliness decays (see `Enclosure.update()`)
        and its temperature is set to track the current `environment`'s
        temperature (added 2026-08-09: `Enclosure.temperature` had no
        other way to ever change after construction - found by actually
        running the wired-up app). Deliberately simple: every enclosure
        tracks the same outdoor temperature exactly, no per-habitat
        climate control.

        Test:
            - Given a zoo with 2 enclosures, when `update_enclosures()`
              is called, then both enclosures' `update()` was called
              exactly once and both now report `environment.temperature`.
            - Given a zoo with zero enclosures (not possible via `Zoo`'s
              own 1..* constructor rule, but defensively), when
              `update_enclosures()` is called, then it simply does
              nothing (no error).
        """
        for enclosure in self._zoo.enclosures:
            enclosure.update(temperature=self._environment.temperature)

    def process_daily_costs(self) -> None:
        """Deduct one day of salary for every employee from the zoo's finances.

        Employees with a `calculate_daily_salary()` of 0 (e.g. unpaid
        volunteers) are skipped, since `FinanceManager.record_expense()`
        rejects non-positive amounts.

        Test:
            - Given a zoo with 2 employees earning 100.0/day combined,
              when `process_daily_costs()` is called, then the zoo's
              FinanceManager balance decreases by 100.0.
            - Given a zoo with an employee whose salary is 0.0, when
              `process_daily_costs()` is called, then no expense is
              recorded for that employee (no ValueError raised).
        """
        for employee in self._zoo.employees:
            daily_salary = employee.calculate_daily_salary()
            if daily_salary > 0:
                self._zoo.finance_manager.record_expense(daily_salary, f"Daily salary: {employee.name}")
