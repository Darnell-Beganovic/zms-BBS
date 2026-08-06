"""Abstract base class for all animals in the simulation.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.domain.behaviors.behavior import Behavior
    from zoo_simulation.domain.food_item import FoodItem

_STAT_MIN = 0
_STAT_MAX = 100


class Animal(ABC):
    """Animal - abstract base class for every animal species in the zoo.

        - Constructor: stores all attributes privately; `health`,
          `hunger` and `energy` can only change through
          `adjust_health()`/`adjust_hunger()`/`adjust_energy()` (never
          assigned directly), which route every change through
          `_validate_value()` so they can never leave the valid 0-100
          range - this is the Kapselung requirement from aufgabe.md
          Teilbereich 2 in code.
        - Composed of 1..* `Behavior` objects (`Animal *-- "1..*" Behavior`
          in the class diagram): `update()` calls `execute(self)` on each
          of them once per simulation tick. At least one Behavior is
          required, enforced in the constructor.
        - _id (int | None): primary key once persisted, None for an
          Animal that has not been saved yet.
        - _name (str): e.g. "Simba".
        - _species (str): e.g. "Lion" - also used as the Single Table
          Inheritance discriminator by AnimalRepository.
        - _age (int): years, >= 0.
        - _health (int): 0-100.
        - _hunger (int): 0-100, higher means hungrier.
        - _energy (int): 0-100.
        - _behaviors (list[Behavior]): the Behavior objects this animal is
          composed of.
    """

    def __init__(
        self,
        name: str,
        species: str,
        behaviors: list[Behavior],
        age: int = 0,
        health: int = 100,
        hunger: int = 0,
        energy: int = 100,
        id: int | None = None,
    ) -> None:
        """Create an Animal with the given attributes.

        Args:
            name (str): e.g. "Simba".
            species (str): e.g. "Lion".
            behaviors (list[Behavior]): at least one Behavior this animal
                is composed of. Raises ValueError if empty, since the
                class diagram's `1..*` multiplicity requires at least
                one.
            age (int, optional): years. Defaults to 0.
            health (int, optional): 0-100. Defaults to 100.
            hunger (int, optional): 0-100. Defaults to 0.
            energy (int, optional): 0-100. Defaults to 100.
            id (int | None, optional): primary key if this Animal was
                loaded from storage. Defaults to None for a new,
                not-yet-persisted Animal.

        Raises:
            ValueError: if `behaviors` is empty.

        Test:
            - Given name="Simba", species="Lion" and a non-empty
              behaviors list, when the constructor is called, then
              `.name` is "Simba" and `.species` is "Lion".
            - Given an empty `behaviors` list, when the constructor is
              called, then a ValueError is raised.
            - Given health=150 (out of range), when the constructor is
              called, then `.health` is clamped to 100.
        """
        if not behaviors:
            raise ValueError("Animal requires at least one Behavior (1..* composition).")
        self._id = id
        self._name = name
        self._species = species
        self._behaviors = list(behaviors)
        self._age = max(0, age)
        self._health = self._validate_value(health)
        self._hunger = self._validate_value(hunger)
        self._energy = self._validate_value(energy)

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def species(self) -> str:
        return self._species

    @property
    def age(self) -> int:
        return self._age

    @property
    def health(self) -> int:
        return self._health

    @property
    def hunger(self) -> int:
        return self._hunger

    @property
    def energy(self) -> int:
        return self._energy

    @property
    def behaviors(self) -> list[Behavior]:
        return list(self._behaviors)

    def _validate_value(self, value: int) -> int:
        """Clamp a stat value into the valid 0-100 range.

        Args:
            value (int): raw value to clamp.

        Returns:
            int: `value` clamped to [0, 100].

        Test:
            - Given value=150, when `_validate_value(150)` is called,
              then it returns 100.
            - Given value=-10, when `_validate_value(-10)` is called,
              then it returns 0.
        """
        return max(_STAT_MIN, min(_STAT_MAX, value))

    def adjust_health(self, delta: int) -> None:
        """Change health by `delta`, clamped to the valid range.

        Args:
            delta (int): amount to add (negative to decrease).

        Test:
            - Given health=90, when `adjust_health(20)` is called, then
              `.health` is 100 (clamped, not 110).
            - Given health=10, when `adjust_health(-50)` is called, then
              `.health` is 0 (clamped, not negative).
        """
        self._health = self._validate_value(self._health + delta)

    def adjust_hunger(self, delta: int) -> None:
        """Change hunger by `delta`, clamped to the valid range.

        Args:
            delta (int): amount to add (negative to decrease).

        Test:
            - Given hunger=5, when `adjust_hunger(-10)` is called, then
              `.hunger` is 0 (clamped, not negative).
            - Given hunger=50, when `adjust_hunger(10)` is called, then
              `.hunger` is 60.
        """
        self._hunger = self._validate_value(self._hunger + delta)

    def adjust_energy(self, delta: int) -> None:
        """Change energy by `delta`, clamped to the valid range.

        Args:
            delta (int): amount to add (negative to decrease).

        Test:
            - Given energy=95, when `adjust_energy(10)` is called, then
              `.energy` is 100 (clamped, not 105).
            - Given energy=30, when `adjust_energy(-40)` is called, then
              `.energy` is 0 (clamped, not negative).
        """
        self._energy = self._validate_value(self._energy + delta)

    def update(self) -> None:
        """Run one simulation tick's worth of composed Behaviors.

        Calls `execute(self)` on every Behavior this animal is composed
        of, in order. Each Behavior affects exactly one stat in
        isolation (see Behavior subclasses) - this method does not add
        any additional cross-behavior logic of its own.

        Test:
            - Given an animal composed of a FeedingBehavior and a
              RestBehavior, when `update()` is called once, then both
              behaviors' effects are applied exactly once (hunger
              decreases, energy/health increase).
            - Given an animal composed of a single Behavior, when
              `update()` is called twice, then that Behavior's effect is
              applied exactly twice (no double-application or skipping).
        """
        for behavior in self._behaviors:
            behavior.execute(self)

    def calculate_welfare(self) -> float:
        """Compute an overall welfare score from health, hunger and energy.

        Returns:
            float: the average of `health`, `100 - hunger` (so lower
                hunger means higher welfare) and `energy`, on a 0-100
                scale.

        Test:
            - Given health=100, hunger=0, energy=100, when
              `calculate_welfare()` is called, then it returns 100.0
              (perfect welfare).
            - Given health=0, hunger=100, energy=0, when
              `calculate_welfare()` is called, then it returns 0.0
              (worst-case welfare).
        """
        return (self._health + (_STAT_MAX - self._hunger) + self._energy) / 3

    @abstractmethod
    def eat(self, food: FoodItem) -> None:
        """Consume the given food to relieve hunger. Species-specific.

        Test:
            - See concrete subclasses (Lion, Giraffe, Penguin) for
              concrete Given/When/Then cases.
        """
        raise NotImplementedError

    @abstractmethod
    def sleep(self) -> None:
        """Rest to recover energy. Species-specific.

        Test:
            - See concrete subclasses (Lion, Giraffe, Penguin) for
              concrete Given/When/Then cases.
        """
        raise NotImplementedError

    @abstractmethod
    def move(self) -> str:
        """Move and describe the movement. Species-specific.

        Test:
            - See concrete subclasses (Lion, Giraffe, Penguin) for
              concrete Given/When/Then cases.
        """
        raise NotImplementedError

    @abstractmethod
    def grow_older(self) -> None:
        """Advance age by one tick/year. Species-specific.

        Test:
            - See concrete subclasses (Lion, Giraffe, Penguin) for
              concrete Given/When/Then cases.
        """
        raise NotImplementedError
