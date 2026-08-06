"""animal_repository.py - repository interface for persisting Animal objects.

    Defines the contract the Backend focus (Darnell) programs against to
    persist/read Animal objects (Lion, Giraffe, Penguin, ...), without
    depending on a concrete database technology (Dependency Inversion
    Principle). get_as_dataframe() additionally feeds ReportService's animal
    report / CSV / Excel export. The only implementation planned is
    SQLAnimalRepository (repositories/sqlite/sqlite_animal_repository.py).
    Schwerpunkt: Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal


class AnimalRepository(ABC):
    """AnimalRepository - abstract interface for Animal persistence.

        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete implementations own their own
          DatabaseConnection.
    """

    @abstractmethod
    def save(self, animal: Animal, enclosure_id: int | None = None) -> int:
        """Persist a new Animal.

        Args:
            animal (Animal): the Animal instance to insert (any concrete
                subclass: Lion, Giraffe, Penguin, ...).
            enclosure_id (int | None, optional): id of the Enclosure the
                animal is assigned to. Animal itself carries no
                enclosure_id attribute (see the class diagram); the
                assignment is passed in the same way
                ZooService.add_animal(animal, enclosure_id) receives it.
                Defaults to None (animal not yet assigned to an
                enclosure).

        Returns:
            int: the animal_id assigned by the database (e.g. read back
            via cursor.lastrowid after the INSERT). Implementations must
            NOT assume the passed-in `animal` instance's `id` is settable
            (Backend domain objects such as Transaction expose `id` as a
            read-only property with no setter) - the caller is
            responsible for making the returned id available on its own
            reference.

        Test:
            - Any implementation, given a new, valid Animal object and an
              existing enclosure_id, when save() is called, must return
              the new animal_id, and that id must be retrievable via
              get_by_id() afterwards with matching data and the correct
              enclosure assignment.
            - Any implementation, given an underlying storage failure
              (e.g. a locked database file), when save() is called, must
              not leave a partially written row behind and must not
              return an id for a row that wasn't committed.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, animal_id: int) -> Animal | None:
        """Retrieve an Animal by its ID.

        Args:
            animal_id (int): primary key of the Animal to load.

        Returns:
            Animal | None: the matching Animal instance, or None if no
            Animal with that ID exists.

        Test:
            - Any implementation, given an animal_id that exists, when
              get_by_id() is called, must return an Animal whose
              attributes match the stored row.
            - Any implementation, given an animal_id that does not exist,
              when get_by_id() is called, must return None instead of
              raising an unhandled exception.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Animal]:
        """Retrieve every stored Animal.

        Returns:
            list[Animal]: all Animal instances currently persisted.

        Test:
            - Any implementation, given 3 stored animals, when get_all()
              is called, must return a list of length 3.
            - Any implementation, given no stored animals, when get_all()
              is called, must return an empty list, not None.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, animal: Animal, enclosure_id: int | None = None) -> None:
        """Persist changes to an existing Animal.

        Args:
            animal (Animal): the Animal instance with updated attribute
                values (e.g. after eat()/sleep()/grow_older()).
            enclosure_id (int | None, optional): id of the Enclosure the
                animal is now assigned to, e.g. after being moved
                (Enclosure.remove_animal() / add_animal()). Defaults to
                None, meaning "leave the current assignment unchanged" -
                see SQLAnimalRepository for the exact semantics.

        Test:
            - Any implementation, given an existing Animal whose hunger
              changed, when update() is called, must make get_by_id()
              return the new value afterwards.
            - Any implementation, given an Animal whose id does not exist
              in storage, when update() is called, must not silently
              create a new row and must not corrupt existing data
              (NFR-09).
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, animal_id: int) -> None:
        """Remove an Animal from storage.

        Args:
            animal_id (int): primary key of the Animal to delete.

        Test:
            - Any implementation, given an animal_id that exists, when
              delete() is called, must make a subsequent get_by_id() for
              that id return None.
            - Any implementation, given an animal_id that does not exist,
              when delete() is called, must not raise an unhandled
              exception (no-op instead of crash).
        """
        raise NotImplementedError

    @abstractmethod
    def get_as_dataframe(self) -> pd.DataFrame:
        """Retrieve every stored Animal as a pandas DataFrame.

        Used by ReportService to build the animal report and export it as
        CSV/Excel.

        Returns:
            pd.DataFrame: one row per Animal, one column per attribute.

        Test:
            - Any implementation, given 3 stored animals, when
              get_as_dataframe() is called, must return a DataFrame with 3
              rows and the expected column names.
            - Any implementation, given no stored animals, when
              get_as_dataframe() is called, must return an empty
              DataFrame with the correct columns (not None), so
              ReportService can still export a valid empty report.
        """
        raise NotImplementedError
