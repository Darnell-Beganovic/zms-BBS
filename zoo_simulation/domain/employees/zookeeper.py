"""Zookeeper employee: feeds animals and cleans enclosures.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.employees.employee import Employee

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal
    from zoo_simulation.domain.enclosure import Enclosure
    from zoo_simulation.domain.food_item import FoodItem


class Zookeeper(Employee):
    """Zookeeper - feeds animals and keeps their enclosures clean."""

    def perform_task(self) -> str:
        """Describe this employee's daily routine. Pure, no side effects.

        Returns:
            str: a human-readable description.

        Test:
            - When `perform_task()` is called, then it returns a
              non-empty string mentioning feeding/cleaning.
            - When called twice, then it returns the same string both
              times (pure, no state change) - actual feeding/cleaning
              happens via `feed_animal()`/`clean_enclosure()` instead.
        """
        return "Feeds the animals and keeps their enclosures clean."

    def feed_animal(self, animal: Animal, food: FoodItem) -> None:
        """Feed an animal with the given food.

        Args:
            animal (Animal): the animal to feed.
            food (FoodItem): the food to feed it with.

        Test:
            - Given a Lion with hunger=50 and a FoodItem with enough
              quantity, when `feed_animal(lion, food)` is called, then
              the lion's hunger decreases (delegates to `animal.eat()`).
            - Given a FoodItem with quantity=0, when `feed_animal()` is
              called, then the animal's hunger stays unchanged (food
              unavailable, see `Animal.eat()`).
        """
        animal.eat(food)

    def clean_enclosure(self, enclosure: Enclosure) -> None:
        """Clean the given enclosure.

        Args:
            enclosure (Enclosure): the enclosure to clean.

        Test:
            - Given an Enclosure with cleanliness=40.0, when
              `clean_enclosure(enclosure)` is called, then the
              enclosure's cleanliness is 100.0 (delegates to
              `enclosure.clean()`).
            - Given an Enclosure already at cleanliness=100.0, when
              `clean_enclosure()` is called, then cleanliness stays
              100.0 (no overflow).
        """
        enclosure.clean()
