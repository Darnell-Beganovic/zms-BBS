"""rest_behavior.py - resting/recovery behavior for an Animal.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.behaviors.behavior import Behavior

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal

_HEALTH_RECOVERY_PER_TICK = 1


class RestBehavior(Behavior):
    """RestBehavior - models an animal resting and recovering.

        - _rest_duration (int): minutes rested this tick. Directly scales
          the energy recovered - a purely linear, single-factor effect,
          kept deliberately simple. Health recovery is a small fixed
          amount, independent of duration.
    """

    def __init__(self, rest_duration: int) -> None:
        """Create a RestBehavior with the given rest duration.

        Args:
            rest_duration (int): minutes rested this tick.

        Test:
            - Given rest_duration=30, when the constructor is called,
              then `.rest_duration` is 30.
            - Given rest_duration=0, when the constructor is called,
              then `.rest_duration` is 0 (no rest - execute() then only
              applies the fixed health recovery, no energy gain).
        """
        self._rest_duration = rest_duration

    @property
    def rest_duration(self) -> int:
        return self._rest_duration

    def execute(self, animal: Animal) -> None:
        """Recover the animal's energy and slightly improve its health.

        Args:
            animal (Animal): the animal to apply this behavior to.

        Test:
            - Given an animal with energy=50 and rest_duration=30, when
              `execute(animal)` is called, then energy increases by 30
              and health increases by 1 (both clamped at 100 by Animal's
              own validation).
            - Given rest_duration=0, when `execute(animal)` is called,
              then energy stays unchanged but health still increases by
              1 (fixed recovery, independent of rest_duration).
        """
        animal.adjust_energy(self._rest_duration)
        animal.adjust_health(_HEALTH_RECOVERY_PER_TICK)
