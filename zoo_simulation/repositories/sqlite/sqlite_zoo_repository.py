"""sqlite_zoo_repository.py - SQLite implementation of ZooRepository.

    Implements ZooRepository (repositories/interfaces/zoo_repository.py)
    against the `zoo` table defined in database/schema.sql, using a
    DatabaseConnection (SQLiteConnection in practice) for all SQL access.
    Assumes the Backend focus's Zoo class exposes id/name/location/
    current_visitors/maximum_visitors as public attributes (matching the
    UML names without the leading underscore) and accepts them as keyword
    arguments in its constructor - this is the integration contract
    implied by the class diagram. Schwerpunkt: Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from zoo_simulation.repositories.interfaces.zoo_repository import ZooRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.zoo import Zoo


class SQLZooRepository(ZooRepository):
    """SQLZooRepository - persists Zoo aggregates in the `zoo` SQLite table.

        - Constructor: stores the DatabaseConnection used for all queries;
          does not open/close the connection itself (owned by the caller,
          e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `zoo` table.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """Store the DatabaseConnection used for all Zoo persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).

        Test:
            - Given a connected DatabaseConnection, when SQLZooRepository
              is constructed, then save()/get_by_id()/update() can be
              called immediately without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection

    def save(self, zoo: Zoo) -> int:
        """Insert a new Zoo row.

        Args:
            zoo (Zoo): the Zoo instance to insert.

        Returns:
            int: the zoo_id assigned by SQLite (cursor.lastrowid). The
            caller is responsible for making the id available on its own
            Zoo reference (e.g. by constructing a new Zoo with this id, or
            however the Backend focus's Zoo class exposes that) - this
            method does not assume `zoo.id` is settable.

        Test:
            - Given a new, valid Zoo object, when save() is called, then
              the returned id is a positive int and get_by_id(that id)
              afterwards returns matching data.
            - Given a database connection failure (e.g. a locked file),
              when save() is called, then the transaction is rolled back,
              no partial row is written, and no id is returned.
        """
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO zoo (name, location, current_visitors, maximum_visitors)
                VALUES (?, ?, ?, ?)
                """,
                (zoo.name, zoo.location, zoo.current_visitors, zoo.maximum_visitors),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_by_id(self, zoo_id: int) -> Zoo | None:
        """Load a single Zoo row by its primary key.

        Args:
            zoo_id (int): primary key of the Zoo to load.

        Returns:
            Zoo | None: the matching Zoo instance, or None if no row with
            that ID exists.

        Test:
            - Given a zoo_id that exists, when get_by_id() is called,
              then the returned Zoo's attributes match the stored row.
            - Given a zoo_id that does not exist, when get_by_id() is
              called, then None is returned instead of raising an
              unhandled exception.
        """
        row = self._connection.execute(
            "SELECT * FROM zoo WHERE zoo_id = ?", (zoo_id,)
        ).fetchone()
        return self._row_to_zoo(row) if row is not None else None

    def update(self, zoo: Zoo) -> None:
        """Update an existing Zoo row.

        Args:
            zoo (Zoo): the Zoo instance with updated attribute values.

        Test:
            - Given an existing Zoo whose current_visitors changed, when
              update() is called, then get_by_id() returns the new value
              afterwards.
            - Given a Zoo whose id does not exist in storage, when
              update() is called, then zero rows are affected and no
              exception is raised (no silent row creation, NFR-09).
        """
        try:
            self._connection.execute(
                """
                UPDATE zoo
                SET name = ?, location = ?, current_visitors = ?, maximum_visitors = ?
                WHERE zoo_id = ?
                """,
                (zoo.name, zoo.location, zoo.current_visitors, zoo.maximum_visitors, zoo.id),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _row_to_zoo(self, row: sqlite3.Row) -> Zoo:
        """Build a Zoo domain object from one `zoo` table row.

        Args:
            row (sqlite3.Row): one row from the `zoo` table (row_factory =
                sqlite3.Row, see SQLiteConnection.connect()).

        Returns:
            Zoo: a Zoo instance populated from the row.

        Test:
            - Given a row with all columns set, when _row_to_zoo() is
              called, then the returned Zoo's attributes equal the row's
              values (row["zoo_id"] -> Zoo.id, etc.).
            - Given a row where location is NULL, when _row_to_zoo() is
              called, then Zoo.location is None instead of raising a
              conversion error.
        """
        from zoo_simulation.domain.zoo import Zoo

        return Zoo(
            id=row["zoo_id"],
            name=row["name"],
            location=row["location"],
            current_visitors=row["current_visitors"],
            maximum_visitors=row["maximum_visitors"],
        )
