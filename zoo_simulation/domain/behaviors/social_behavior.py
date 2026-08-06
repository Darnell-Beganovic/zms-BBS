"""social_behavior.py - social interaction behavior for an Animal.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.behaviors.behavior import Behavior

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal


class SocialBehavior(Behavior):
    """SocialBehavior - models an animal's social interaction with its group.

        - _social_level (int): how social this animal is, 0-100. Directly
          scales the energy gained each tick - a purely linear,
          single-factor effect, kept deliberately simple.
    """

    def __init__(self, social_level: int) -> None:
        """Create a SocialBehavior with the given social level.

        Args:
            social_level (int): 0-100, higher means more energy gained
                from social interaction each tick.

        Test:
            - Given social_level=80, when the constructor is called,
              then `.social_level` is 80.
            - Given social_level=0, when the constructor is called, then
              `.social_level` is 0 (a purely solitary animal - execute()
              then has no effect).
        """
        self._social_level = social_level

    @property
    def social_level(self) -> int:
        return self._social_level

    def execute(self, animal: Animal) -> None:
        """Boost the animal's energy proportionally to its social level.

        Args:
            animal (Animal): the animal to apply this behavior to.

        Test:
            - Given an animal with energy=50 and social_level=20, when
              `execute(animal)` is called, then energy increases by 2
              (social_level // 10, clamped at 100 by Animal's own
              validation).
            - Given social_level=0, when `execute(animal)` is called,
              then the animal's energy stays unchanged.
        """
        animal.adjust_energy(self._social_level // 10)
