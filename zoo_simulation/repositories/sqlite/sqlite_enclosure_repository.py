"""sqlite_enclosure_repository.py - SQLite implementation of EnclosureRepository.

    Implements EnclosureRepository
    (repositories/interfaces/enclosure_repository.py) against the
    `enclosure` table defined in database/schema.sql, using a
    DatabaseConnection (SQLiteConnection in practice) for all SQL access.
    Assumes the Backend focus's Enclosure class exposes id/name/
    enclosure_type/size/capacity/cleanliness/temperature as public
    attributes (matching the UML names without the leading underscore) and
    accepts them as keyword arguments in its constructor - this is the
    integration contract implied by the class diagram. Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from zoo_simulation.repositories.interfaces.enclosure_repository import EnclosureRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.enclosure import Enclosure


class SQLEnclosureRepository(EnclosureRepository):
    """SQLEnclosureRepository - persists Enclosure objects in the `enclosure` table.

        - Constructor: stores the DatabaseConnection used for all queries;
          does not open/close the connection itself (owned by the caller,
          e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `enclosure` table.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """Store the DatabaseConnection used for all Enclosure persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).

        Test:
            - Given a connected DatabaseConnection, when
              SQLEnclosureRepository is constructed, then
              save()/get_by_id()/get_all()/update() can be called
              immediately without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection

    def save(self, enclosure: Enclosure, zoo_id: int) -> int:
        """Insert a new Enclosure row.

        Args:
            enclosure (Enclosure): the Enclosure instance to insert.
            zoo_id (int): id of the Zoo the enclosure belongs to. Enclosure
                carries no zoo_id attribute (see the class diagram), so it
                is supplied separately, mirroring how AnimalRepository
                takes enclosure_id separately.

        Returns:
            int: the enclosure_id assigned by SQLite (cursor.lastrowid).
            The caller is responsible for making the id available on its
            own Enclosure reference - this method does not assume
            `enclosure.id` is settable.

        Test:
            - Given a new, valid Enclosure object and an existing zoo_id,
              when save() is called, then the returned id is a positive
              int and get_by_id(that id) afterwards returns matching data.
            - Given a database connection failure (e.g. a locked file),
              when save() is called, then the transaction is rolled back,
              no partial row is written, and no id is returned.
        """
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO enclosure
                    (zoo_id, name, enclosure_type, size, capacity, cleanliness, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    zoo_id,
                    enclosure.name,
                    enclosure.enclosure_type,
                    enclosure.size,
                    enclosure.capacity,
                    enclosure.cleanliness,
                    enclosure.temperature,
                ),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_by_id(self, enclosure_id: int) -> Enclosure | None:
        """Load a single Enclosure row by its primary key.

        Args:
            enclosure_id (int): primary key of the Enclosure to load.

        Returns:
            Enclosure | None: the matching Enclosure instance, or None if
            no row with that ID exists.

        Test:
            - Given an enclosure_id that exists, when get_by_id() is
              called, then the returned Enclosure's attributes match the
              stored row.
            - Given an enclosure_id that does not exist, when get_by_id()
              is called, then None is returned instead of raising an
              unhandled exception.
        """
        row = self._connection.execute(
            "SELECT * FROM enclosure WHERE enclosure_id = ?", (enclosure_id,)
        ).fetchone()
        return self._row_to_enclosure(row) if row is not None else None

    def get_all(self) -> list[Enclosure]:
        """Load every stored Enclosure row.

        Returns:
            list[Enclosure]: all Enclosure instances currently persisted.

        Test:
            - Given 2 stored enclosures, when get_all() is called, then a
              list of length 2 is returned.
            - Given no stored enclosures, when get_all() is called, then
              an empty list is returned, not None.
        """
        rows = self._connection.execute("SELECT * FROM enclosure").fetchall()
        return [self._row_to_enclosure(row) for row in rows]

    def update(self, enclosure: Enclosure) -> None:
        """Update an existing Enclosure row.

        Args:
            enclosure (Enclosure): the Enclosure instance with updated
                attribute values (e.g. after clean()/update()).

        Test:
            - Given an existing Enclosure whose cleanliness changed, when
              update() is called, then get_by_id() returns the new value
              afterwards.
            - Given an Enclosure whose id does not exist in storage, when
              update() is called, then zero rows are affected and no
              exception is raised (no silent row creation, NFR-09).
        """
        try:
            self._connection.execute(
                """
                UPDATE enclosure
                SET name = ?, enclosure_type = ?, size = ?, capacity = ?,
                    cleanliness = ?, temperature = ?
                WHERE enclosure_id = ?
                """,
                (
                    enclosure.name,
                    enclosure.enclosure_type,
                    enclosure.size,
                    enclosure.capacity,
                    enclosure.cleanliness,
                    enclosure.temperature,
                    enclosure.id,
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _row_to_enclosure(self, row: sqlite3.Row) -> Enclosure:
        """Build an Enclosure domain object from one `enclosure` table row.

        Args:
            row (sqlite3.Row): one row from the `enclosure` table
                (row_factory = sqlite3.Row, see
                SQLiteConnection.connect()).

        Returns:
            Enclosure: an Enclosure instance populated from the row.

        Test:
            - Given a row with all columns set, when _row_to_enclosure()
              is called, then the returned Enclosure's attributes equal
              the row's values (row["enclosure_id"] -> Enclosure.id,
              etc.).
            - Given a row where enclosure_type is NULL, when
              _row_to_enclosure() is called, then
              Enclosure.enclosure_type is None instead of raising a
              conversion error.
        """
        from zoo_simulation.domain.enclosure import Enclosure

        return Enclosure(
            id=row["enclosure_id"],
            name=row["name"],
            enclosure_type=row["enclosure_type"],
            size=row["size"],
            capacity=row["capacity"],
            cleanliness=row["cleanliness"],
            temperature=row["temperature"],
        )
