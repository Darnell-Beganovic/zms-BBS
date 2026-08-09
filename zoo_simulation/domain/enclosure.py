"""Enclosure: houses a group of animals.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal

_CLEANLINESS_MAX = 100.0
_CLEANLINESS_DECAY_PER_TICK = 5.0


class Enclosure:
    """Enclosure - a habitat that houses a group of animals.

    Enclosure aggregates Animal (`Enclosure o-- "0..*" Animal`, not
    composition): an Animal is not owned exclusively by its Enclosure and
    can exist without one (see planning_db_kaiss.md's note on
    AnimalRepository - Animal carries no persisted enclosure_id
    attribute of its own).

        - Constructor: stores all attributes privately; `cleanliness`
          only changes through `clean()`/`update()`, never assigned
          directly.
        - _id (int | None): primary key once persisted, None for an
          Enclosure that has not been saved yet.
        - _name (str): e.g. "Savannah Habitat".
        - _enclosure_type (str): e.g. "savannah", "aquatic".
        - _size (float): area, e.g. in square meters.
        - _capacity (int): maximum number of animals this enclosure can
          house.
        - _cleanliness (float): 0-100, decays over time via `update()`,
          reset to maximum via `clean()`.
        - _temperature (float): degrees, e.g. Celsius.
        - _animals (list[Animal]): animals currently housed here
          (aggregation, see above).
    """

    def __init__(
        self,
        name: str,
        enclosure_type: str,
        size: float,
        capacity: int,
        cleanliness: float = 100.0,
        temperature: float = 20.0,
        id: int | None = None,
    ) -> None:
        """Create an Enclosure with the given attributes.

        Args:
            name (str): e.g. "Savannah Habitat".
            enclosure_type (str): e.g. "savannah", "aquatic".
            size (float): area, e.g. in square meters.
            capacity (int): maximum number of animals.
            cleanliness (float, optional): 0-100. Defaults to 100.0
                (freshly built/cleaned).
            temperature (float, optional): degrees. Defaults to 20.0.
            id (int | None, optional): primary key if loaded from
                storage. Defaults to None for a new, not-yet-persisted
                Enclosure.

        Test:
            - Given name="Savannah Habitat" and capacity=5, when the
              constructor is called, then `.capacity` is 5 and
              `.animals` is an empty list.
            - Given no `cleanliness` is passed, when the constructor is
              called, then `.cleanliness` is 100.0 (default).
        """
        self._id = id
        self._name = name
        self._enclosure_type = enclosure_type
        self._size = size
        self._capacity = capacity
        self._cleanliness = cleanliness
        self._temperature = temperature
        self._animals: list[Animal] = []

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def enclosure_type(self) -> str:
        return self._enclosure_type

    @property
    def size(self) -> float:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def cleanliness(self) -> float:
        return self._cleanliness

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def animals(self) -> list[Animal]:
        return list(self._animals)

    def has_capacity(self) -> bool:
        """Check whether another animal can still be added.

        Returns:
            bool: True if fewer animals are housed than `capacity`,
                False otherwise.

        Test:
            - Given capacity=2 and 1 animal housed, when
              `has_capacity()` is called, then it returns True.
            - Given capacity=2 and 2 animals housed, when
              `has_capacity()` is called, then it returns False.
        """
        return len(self._animals) < self._capacity

    def add_animal(self, animal: Animal) -> None:
        """Add an animal to this enclosure.

        Args:
            animal (Animal): the animal to house here.

        Raises:
            ValueError: if `has_capacity()` is False - callers are
                expected to check `has_capacity()` first (e.g.
                ZooService.add_animal()) if they want to handle a full
                enclosure without a try/except.

        Test:
            - Given an Enclosure with capacity=2 and 1 animal housed,
              when `add_animal(animal)` is called, then `.animals` has 2
              entries.
            - Given an Enclosure at full capacity, when `add_animal()` is
              called, then a ValueError is raised and `.animals` stays
              unchanged.
        """
        if not self.has_capacity():
            raise ValueError(f"Enclosure {self._name!r} is at full capacity ({self._capacity}).")
        self._animals.append(animal)

    def remove_animal(self, animal_id: int) -> None:
        """Remove an animal by its ID, if housed here.

        Args:
            animal_id (int): id of the animal to remove.

        Test:
            - Given an Enclosure housing an animal with id=3, when
              `remove_animal(3)` is called, then `.animals` no longer
              contains that animal.
            - Given an animal_id not housed here, when `remove_animal()`
              is called, then `.animals` stays unchanged (no error
              raised).
        """
        self._animals = [animal for animal in self._animals if animal.id != animal_id]

    def clean(self) -> None:
        """Clean the enclosure, resetting cleanliness to its maximum.

        Test:
            - Given cleanliness=40.0, when `clean()` is called, then
              `.cleanliness` is 100.0.
            - Given cleanliness=100.0 already, when `clean()` is called,
              then `.cleanliness` stays 100.0 (no overflow).
        """
        self._cleanliness = _CLEANLINESS_MAX

    def update(self) -> None:
        """Advance one simulation tick: cleanliness decays over time.

        Test:
            - Given cleanliness=100.0, when `update()` is called, then
              `.cleanliness` is 95.0.
            - Given cleanliness=2.0, when `update()` is called, then
              `.cleanliness` is 0.0 (clamped, not negative).
        """
        self._cleanliness = max(0.0, self._cleanliness - _CLEANLINESS_DECAY_PER_TICK)
