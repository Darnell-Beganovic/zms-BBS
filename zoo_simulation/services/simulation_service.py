"""SimulationService: exposes the SimulationEngine to the controller layer.

Schwerpunkt: Backend (Service Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.simulation.simulation_engine import SimulationEngine


class SimulationService:
    """SimulationService - a thin facade over SimulationEngine for the controller layer.

    Single Responsibility: SimulationEngine advances simulation state,
    SimulationService only exposes that capability in the shape
    ZooController needs (run one/many steps, read the clock) - it adds
    no logic of its own.

        - Constructor: stores the SimulationEngine privately.
        - _simulation_engine (SimulationEngine): the engine being
          driven.
    """

    def __init__(self, simulation_engine: SimulationEngine) -> None:
        """Store the SimulationEngine this service drives.

        Args:
            simulation_engine (SimulationEngine): the engine to expose.

        Test:
            - Given a SimulationEngine at current_step=0, when
              SimulationService is constructed, then
              `get_simulation_time()` returns 0.
            - Given the same SimulationEngine instance, when two
              SimulationService objects wrap it, then advancing one
              (`run_step()`) is reflected in the other's
              `get_simulation_time()` too (shared engine, not copied).
        """
        self._simulation_engine = simulation_engine

    def run_step(self) -> None:
        """Advance the simulation by exactly one tick.

        Test:
            - Given current_step=0, when `run_step()` is called, then
              `get_simulation_time()` returns 1.
            - Given a zoo with animals, when `run_step()` is called,
              then their state changes exactly as `SimulationEngine.tick()`
              describes (delegates directly, no extra logic).
        """
        self._simulation_engine.tick()

    def run_steps(self, number_of_steps: int) -> None:
        """Advance the simulation by several ticks in a row.

        Args:
            number_of_steps (int): how many ticks to run. Non-positive
                values run zero ticks (Python's `range()` semantics), no
                error is raised.

        Test:
            - Given current_step=0, when `run_steps(3)` is called, then
              `get_simulation_time()` returns 3.
            - Given number_of_steps=0, when `run_steps(0)` is called,
              then `get_simulation_time()` stays unchanged (no ticks
              run).
        """
        for _ in range(number_of_steps):
            self._simulation_engine.tick()

    def get_simulation_time(self) -> int:
        """Return the current simulation clock.

        Returns:
            int: the number of ticks run so far.

        Test:
            - Given `run_steps(5)` was called, when
              `get_simulation_time()` is called, then it returns 5.
            - Given no steps were run yet, when `get_simulation_time()`
              is called, then it returns 0.
        """
        return self._simulation_engine.current_step
