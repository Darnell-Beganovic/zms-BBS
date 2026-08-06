"""feeding_behavior.py - passive foraging/grazing behavior for an Animal.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.behaviors.behavior import Behavior

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal

_HUNGER_RELIEF_PER_TICK = 5


class FeedingBehavior(Behavior):
    """FeedingBehavior - models an animal foraging/grazing on its own.

    Distinct from Animal.eat(food): this is passive, does not consume any
    FoodItem/Inventory stock, and only slightly relieves hunger each tick
    - it models background foraging, not an actual feeding by staff.

        - _food_preference (str): the animal's preferred food type, kept
          for documentation/diagram purposes; the current, deliberately
          simple execute() does not vary its effect by preference.
    """

    def __init__(self, food_preference: str) -> None:
        """Create a FeedingBehavior for a given food preference.

        Args:
            food_preference (str): e.g. "meat", "leaves", "fish".

        Test:
            - Given food_preference="meat", when the constructor is
              called, then `.food_preference` is "meat".
            - Given food_preference="", when the constructor is called,
              then `.food_preference` is "" (no validation performed
              here - an empty preference is a data-quality concern, not
              a structural one).
        """
        self._food_preference = food_preference

    @property
    def food_preference(self) -> str:
        return self._food_preference

    def execute(self, animal: Animal) -> None:
        """Slightly relieve the animal's hunger through passive foraging.

        Args:
            animal (Animal): the animal to apply this behavior to.

        Test:
            - Given an animal with hunger=50, when `execute(animal)` is
              called, then hunger decreases by 5 (clamped at 0 by
              Animal's own validation).
            - Given an animal with hunger=0, when `execute(animal)` is
              called, then hunger stays 0 (no negative hunger).
        """
        animal.adjust_hunger(-_HUNGER_RELIEF_PER_TICK)
