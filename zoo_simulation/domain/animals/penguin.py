"""Penguin: concrete animal species.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.animals.animal import Animal

if TYPE_CHECKING:
    from zoo_simulation.domain.behaviors.behavior import Behavior
    from zoo_simulation.domain.food_item import FoodItem

_EAT_AMOUNT = 1.0
_HUNGER_RELIEF = 25
_SLEEP_ENERGY_GAIN = 20
_MOVE_ENERGY_COST = 4
_OLD_AGE_THRESHOLD = 15
_OLD_AGE_HEALTH_PENALTY = 2


class Penguin(Animal):
    """Penguin - small carnivore that eats little and often, in a colony.

        - _food_preference (str): defaults to "fish"; kept for
          documentation/diagram purposes, `eat()` itself does not check
          it (any FoodItem with enough quantity is accepted, matching
          `Animal.eat()`'s void/no-return-value contract).
    """

    def __init__(
        self,
        name: str,
        behaviors: list[Behavior],
        age: int = 0,
        health: int = 100,
        hunger: int = 0,
        energy: int = 100,
        id: int | None = None,
        food_preference: str = "fish",
    ) -> None:
        """Create a Penguin.

        Args:
            name (str): e.g. "Pingu".
            behaviors (list[Behavior]): at least one Behavior this
                penguin is composed of.
            age (int, optional): years. Defaults to 0.
            health (int, optional): 0-100. Defaults to 100.
            hunger (int, optional): 0-100. Defaults to 0.
            energy (int, optional): 0-100. Defaults to 100.
            id (int | None, optional): primary key if loaded from
                storage. Defaults to None.
            food_preference (str, optional): Defaults to "fish".

        Test:
            - Given name="Pingu" and a non-empty behaviors list, when
              the constructor is called, then `.species` is "Penguin"
              and `.food_preference` is "fish" (default).
            - Given food_preference="krill" explicitly, when the
              constructor is called, then `.food_preference` is "krill".
        """
        super().__init__(
            name=name,
            species="Penguin",
            behaviors=behaviors,
            age=age,
            health=health,
            hunger=hunger,
            energy=energy,
            id=id,
        )
        self._food_preference = food_preference

    @property
    def food_preference(self) -> str:
        return self._food_preference

    def eat(self, food: FoodItem) -> None:
        """Eat a small portion of fish, moderately relieving hunger.

        Args:
            food (FoodItem): the food item to consume from.

        Test:
            - Given a Penguin with hunger=50 and a FoodItem with
              quantity=10.0, when `eat(food)` is called, then hunger
              decreases by 25 and 1.0 unit is consumed from `food`.
            - Given a Penguin and a FoodItem with quantity=0, when
              `eat(food)` is called, then hunger stays unchanged (food
              unavailable, no consumption happens).
        """
        if food.decrease_quantity(_EAT_AMOUNT):
            self.adjust_hunger(-_HUNGER_RELIEF)

    def sleep(self) -> None:
        """Sleep in short bursts, moderately recovering energy.

        Test:
            - Given energy=50, when `sleep()` is called, then energy
              increases by 20.
            - Given energy=90, when `sleep()` is called, then energy is
              clamped to 100 (not 110).
        """
        self.adjust_energy(_SLEEP_ENERGY_GAIN)

    def move(self) -> str:
        """Waddle and occasionally slide, at a small energy cost.

        Returns:
            str: a description of the penguin's movement.

        Test:
            - Given energy=50, when `move()` is called, then it returns
              a non-empty description and energy decreases by 4.
            - Given energy=0, when `move()` is called, then energy stays
              0 (clamped, not negative).
        """
        self.adjust_energy(-_MOVE_ENERGY_COST)
        return f"{self.name} waddles along and slides on its belly."

    def grow_older(self) -> None:
        """Advance age by one year; past old age, health slowly declines.

        Test:
            - Given age=5, when `grow_older()` is called, then age is 6
              and health is unaffected.
            - Given age=15 (at the old-age threshold), when
              `grow_older()` is called, then age is 16 and health
              decreases by 2.
        """
        self._age += 1
        if self._age > _OLD_AGE_THRESHOLD:
            self.adjust_health(-_OLD_AGE_HEALTH_PENALTY)

    def typical_behavior(self) -> str:
        """Describe this species' typical behavior.

        Returns:
            str: a human-readable description.

        Test:
            - When `typical_behavior()` is called, then it returns a
              non-empty string mentioning swimming/colony behavior.
            - When called twice, then it returns the same string both
              times (pure, no state change).
        """
        return "Swims and dives for fish, then huddles together with the colony."
