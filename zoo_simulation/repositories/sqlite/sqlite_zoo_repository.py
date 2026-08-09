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

    Fixed 2026-08-09: `_row_to_zoo()` previously called `Zoo(...)` without
    `enclosures`/`inventory`/`finance_manager`, all required positional
    arguments (`Zoo *-- "1..*" Enclosure`, `Zoo *-- "1" Inventory`,
    `Zoo *-- "1" FinanceManager`) - every `get_by_id()` call raised
    `TypeError`. None of these three are columns on the `zoo` table (they
    live in their own tables/aren't persisted at all for FinanceManager),
    so `SQLZooRepository` now composes `EnclosureRepository`,
    `InventoryRepository` and `FinanceRepository` to load them - the same
    Dependency Inversion the other repositories already use, just one
    level up since `Zoo` is the aggregate root. See planning_db_kaiss.md
    section 6 for the single-zoo scoping assumption this relies on
    (`EnclosureRepository.get_all()`/`FinanceRepository.get_balance()`
    have no zoo_id filter, matching every other place in this codebase
    that assumes exactly one Zoo).
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from zoo_simulation.domain.finance_manager import FinanceManager
from zoo_simulation.domain.inventory import Inventory
from zoo_simulation.repositories.interfaces.zoo_repository import ZooRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.zoo import Zoo
    from zoo_simulation.repositories.interfaces.enclosure_repository import EnclosureRepository
    from zoo_simulation.repositories.interfaces.finance_repository import FinanceRepository
    from zoo_simulation.repositories.interfaces.inventory_repository import InventoryRepository


class SQLZooRepository(ZooRepository):
    """SQLZooRepository - persists Zoo aggregates in the `zoo` SQLite table.

        - Constructor: stores the DatabaseConnection used for all queries,
          plus the three sibling repositories needed to reconstruct a full
          Zoo aggregate (see module docstring, "Fixed 2026-08-09"); does
          not open/close the connection itself (owned by the caller, e.g.
          main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `zoo` table.
        - _enclosure_repository (EnclosureRepository): loads the
          Enclosures a reconstructed Zoo owns.
        - _inventory_repository (InventoryRepository): loads the Inventory
          a reconstructed Zoo owns.
        - _finance_repository (FinanceRepository): loads the balance used
          to build the FinanceManager a reconstructed Zoo owns.
    """

    def __init__(
        self,
        connection: DatabaseConnection,
        enclosure_repository: EnclosureRepository,
        inventory_repository: InventoryRepository,
        finance_repository: FinanceRepository,
    ) -> None:
        """Store the DatabaseConnection and sibling repositories used for Zoo persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).
            enclosure_repository (EnclosureRepository): used by
                `_row_to_zoo()` to load a reconstructed Zoo's Enclosures.
            inventory_repository (InventoryRepository): used by
                `_row_to_zoo()` to load a reconstructed Zoo's Inventory.
            finance_repository (FinanceRepository): used by
                `_row_to_zoo()` to load the balance for a reconstructed
                Zoo's FinanceManager.

        Test:
            - Given a connected DatabaseConnection and the three sibling
              repositories, when SQLZooRepository is constructed, then
              save()/get_by_id()/update() can be called immediately
              without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects (including the three passed in here),
              when both are used, then they operate against the same
              underlying database file and transaction.
        """
        self._connection = connection
        self._enclosure_repository = enclosure_repository
        self._inventory_repository = inventory_repository
        self._finance_repository = finance_repository

    def save(self, zoo: Zoo) -> int:
        """Insert a new Zoo row.

        Only writes the `zoo` table's own columns (name/location/
        visitors) - `zoo.enclosures`/`zoo.inventory`/`zoo.finance_manager`
        are NOT cascade-persisted, the same way `EnclosureRepository.save()`
        takes `zoo_id` separately rather than being reachable from
        `ZooRepository.save()`. The caller is responsible for also saving
        each Enclosure (via `EnclosureRepository.save(enclosure, zoo_id)`
        with the id returned here) and any Inventory items before relying
        on `get_by_id()` for this zoo - see the Test note below and
        planning_db_kaiss.md section 6 ("save() does not cascade").

        Args:
            zoo (Zoo): the Zoo instance to insert.

        Returns:
            int: the zoo_id assigned by SQLite (cursor.lastrowid). The
            caller is responsible for making the id available on its own
            Zoo reference (e.g. by constructing a new Zoo with this id, or
            however the Backend focus's Zoo class exposes that) - this
            method does not assume `zoo.id` is settable.

        Test:
            - Given a new, valid Zoo object whose Enclosures were also
              separately saved via `EnclosureRepository.save(enclosure,
              zoo_id)` using the id returned here, when save() is called
              and then get_by_id(that id), then the returned id is a
              positive int and get_by_id() affords matching data
              including those Enclosures.
            - Given a new, valid Zoo object whose Enclosures were NOT also
              separately saved (save() does not cascade, see above), when
              save() is called and then get_by_id(that id), then
              get_by_id() raises `ValueError` - `Zoo` requires at least
              one Enclosure (`1..*` composition) and none were persisted,
              not a bug in get_by_id() itself.
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

        Loads the full aggregate, not just the `zoo` row's own columns:
        Enclosures via `_enclosure_repository`, Inventory via
        `_inventory_repository` (falling back to an empty `Inventory()` if
        this zoo has no `inventory` row yet), and a `FinanceManager`
        seeded from `_finance_repository.get_balance()` (see module
        docstring, "Fixed 2026-08-09").

        Args:
            row (sqlite3.Row): one row from the `zoo` table (row_factory =
                sqlite3.Row, see SQLiteConnection.connect()).

        Returns:
            Zoo: a Zoo instance populated from the row plus its composed
            Enclosures/Inventory/FinanceManager.

        Raises:
            ValueError: propagated from `Zoo.__init__()` if this zoo has
                zero Enclosures - `Zoo` requires at least one (`1..*`
                composition), the same rule enforced when a Zoo is first
                created, not a new restriction added here.

        Test:
            - Given a row with all columns set and 2 Enclosures already
              saved, when _row_to_zoo() is called, then the returned
              Zoo's attributes equal the row's values (row["zoo_id"] ->
              Zoo.id, etc.) and `.enclosures` has length 2.
            - Given a row where location is NULL, when _row_to_zoo() is
              called, then Zoo.location is None instead of raising a
              conversion error.
        """
        from zoo_simulation.domain.zoo import Zoo

        zoo_id = row["zoo_id"]
        enclosures = self._enclosure_repository.get_all()
        inventory = self._inventory_repository.get_inventory(zoo_id) or Inventory()
        finance_manager = FinanceManager(balance=self._finance_repository.get_balance())

        return Zoo(
            id=zoo_id,
            name=row["name"],
            location=row["location"],
            current_visitors=row["current_visitors"],
            maximum_visitors=row["maximum_visitors"],
            enclosures=enclosures,
            inventory=inventory,
            finance_manager=finance_manager,
        )
