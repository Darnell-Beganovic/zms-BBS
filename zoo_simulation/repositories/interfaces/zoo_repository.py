"""zoo_repository.py - repository interface for persisting Zoo aggregates.
    Defines the contract the Backend focus (Darnell) programs against to
    persist/read Zoo objects, without depending on a concrete database
    technology (Dependency Inversion Principle). The only implementation
    planned is SQLZooRepository
    (repositories/sqlite/sqlite_zoo_repository.py). Schwerpunkt: Datenbank -
    Kaiss Saleh.
    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from zoo_simulation.domain.zoo import Zoo
class ZooRepository(ABC):
    """ZooRepository - abstract interface for Zoo persistence.
        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete implementations own their own
          DatabaseConnection.
    """
    @abstractmethod
    def save(self, zoo: Zoo) -> int:
        """Persist a new Zoo aggregate.
        Args:
            zoo (Zoo): the Zoo instance to insert.
        Returns:
            int: the zoo_id assigned by the database (e.g. read back via
            cursor.lastrowid after the INSERT). Implementations must also
            set this id on the passed-in `zoo` instance before returning,
            so the caller's reference is immediately usable for
            get_by_id()/update() without a re-fetch.
        Test:
            - Any implementation, given a new, valid Zoo object, when
              save() is called, must return the new zoo_id, and that id
              must be retrievable via get_by_id() afterwards with
              matching data.
            - Any implementation, given a new, valid Zoo object, when
              save() is called, must also set zoo.id to the returned
              value.
            - Any implementation, given a Zoo with an id that already
              exists, when save() is called, must not silently create a
              conflicting duplicate row (update() exists separately for
              modifying an existing Zoo).
        """
        raise NotImplementedError
    @abstractmethod
    def get_by_id(self, zoo_id: int) -> Zoo | None:
        """Retrieve a Zoo aggregate by its ID.
        Args:
            zoo_id (int): primary key of the Zoo to load.
        Returns:
            Zoo | None: the matching Zoo instance, or None if no Zoo with
            that ID exists.
        Test:
            - Any implementation, given a zoo_id that exists, when
              get_by_id() is called, must return a Zoo whose attributes
              match the stored row.
            - Any implementation, given a zoo_id that does not exist, when
              get_by_id() is called, must return None instead of raising
              an unhandled exception.
        """
        raise NotImplementedError
    @abstractmethod
    def update(self, zoo: Zoo) -> None:
        """Persist changes to an existing Zoo aggregate.
        Args:
            zoo (Zoo): the Zoo instance with updated attribute values.
        Test:
            - Any implementation, given an existing Zoo whose
              current_visitors changed, when update() is called, must make
              get_by_id() return the new value afterwards.
            - Any implementation, given a Zoo whose id does not exist in
              storage, when update() is called, must not silently create a
              new row and must not corrupt existing data (NFR-09).
        """
        raise NotImplementedError
