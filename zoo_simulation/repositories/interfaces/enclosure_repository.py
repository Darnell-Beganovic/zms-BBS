"""enclosure_repository.py - repository interface for persisting Enclosure objects.

    Defines the contract the Backend focus (Darnell) programs against to
    persist/read Enclosure objects, without depending on a concrete database
    technology (Dependency Inversion Principle). The only implementation
    planned is SQLEnclosureRepository
    (repositories/sqlite/sqlite_enclosure_repository.py). Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.domain.enclosure import Enclosure


class EnclosureRepository(ABC):
    """EnclosureRepository - abstract interface for Enclosure persistence.

        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete implementations own their own
          DatabaseConnection.
    """

    @abstractmethod
    def save(self, enclosure: Enclosure, zoo_id: int) -> int:
        """Persist a new Enclosure.

        Args:
            enclosure (Enclosure): the Enclosure instance to insert.
            zoo_id (int): id of the Zoo the enclosure belongs to. Enclosure
                itself carries no zoo_id attribute (see the class
                diagram); this mirrors how AnimalRepository.save() takes
                enclosure_id separately since Animal carries no
                enclosure_id attribute either.

        Returns:
            int: the enclosure_id assigned by the database (e.g. read
            back via cursor.lastrowid after the INSERT). Implementations
            must also set this id on the passed-in `enclosure` instance
            before returning, so the caller's reference is immediately
            usable for get_by_id()/update() without a re-fetch.

        Test:
            - Any implementation, given a new, valid Enclosure object and
              an existing zoo_id, when save() is called, must return the
              new enclosure_id, and that id must be retrievable via
              get_by_id() afterwards with matching data.
            - Any implementation, given a new, valid Enclosure object,
              when save() is called, must also set enclosure.id to the
              returned value.
            - Any implementation, given an Enclosure with an id that
              already exists, when save() is called, must not silently
              create a conflicting duplicate row (update() exists
              separately for modifying an existing Enclosure).
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, enclosure_id: int) -> Enclosure | None:
        """Retrieve an Enclosure by its ID.

        Args:
            enclosure_id (int): primary key of the Enclosure to load.

        Returns:
            Enclosure | None: the matching Enclosure instance, or None if
            no Enclosure with that ID exists.

        Test:
            - Any implementation, given an enclosure_id that exists, when
              get_by_id() is called, must return an Enclosure whose
              attributes match the stored row.
            - Any implementation, given an enclosure_id that does not
              exist, when get_by_id() is called, must return None instead
              of raising an unhandled exception.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Enclosure]:
        """Retrieve every stored Enclosure.

        Returns:
            list[Enclosure]: all Enclosure instances currently persisted.

        Test:
            - Any implementation, given 2 stored enclosures, when
              get_all() is called, must return a list of length 2.
            - Any implementation, given no stored enclosures, when
              get_all() is called, must return an empty list, not None.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, enclosure: Enclosure) -> None:
        """Persist changes to an existing Enclosure.

        Args:
            enclosure (Enclosure): the Enclosure instance with updated
                attribute values (e.g. after clean()/update()).

        Test:
            - Any implementation, given an existing Enclosure whose
              cleanliness changed, when update() is called, must make
              get_by_id() return the new value afterwards.
            - Any implementation, given an Enclosure whose id does not
              exist in storage, when update() is called, must not
              silently create a new row and must not corrupt existing
              data (NFR-09).
        """
        raise NotImplementedError
