"""sqlite_inventory_repository.py - SQLite implementation of InventoryRepository.

    Implements InventoryRepository
    (repositories/interfaces/inventory_repository.py) against the
    `food_item` and `medication` tables defined in database/schema.sql,
    using a DatabaseConnection (SQLiteConnection in practice) for all SQL
    access. FoodItem and Medication get parallel method sets because
    Inventory composes them as two separate collections in the class
    diagram (Inventory *-- FoodItem, Inventory *-- Medication) and they
    live in two separate tables. Assumes FoodItem/Medication constructors
    accept id/name/quantity/minimum_quantity as keyword arguments
    (FoodItem additionally food_type/price_per_unit). Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pandas as pd

from zoo_simulation.repositories.interfaces.inventory_repository import InventoryRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.food_item import FoodItem
    from zoo_simulation.domain.medication import Medication

_COMBINED_COLUMNS = (
    "id",
    "item_type",
    "name",
    "food_type",
    "quantity",
    "price_per_unit",
    "minimum_quantity",
)


class SQLInventoryRepository(InventoryRepository):
    """SQLInventoryRepository - persists FoodItem/Medication in their tables.

        - Constructor: stores the DatabaseConnection used for all queries;
          does not open/close the connection itself (owned by the caller,
          e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `food_item` and `medication` tables.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """Store the DatabaseConnection used for all Inventory persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).

        Test:
            - Given a connected DatabaseConnection, when
              SQLInventoryRepository is constructed, then all save/get/
              update methods can be called immediately without any
              further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection

    def save_item(self, item: FoodItem, inventory_id: int) -> int:
        """Insert a new FoodItem row.

        Args:
            item (FoodItem): the FoodItem instance to insert.
            inventory_id (int): id of the Inventory the item belongs to.

        Returns:
            int: the food_id assigned by SQLite (cursor.lastrowid). The
            caller is responsible for making the id available on its own
            FoodItem reference - this method does not assume `item.id` is
            settable (FoodItem exposes `id` as a read-only property with
            no setter).

        Test:
            - Given a new, valid FoodItem and an existing inventory_id,
              when save_item() is called, then the returned id is a
              positive int and get_item() afterwards returns matching
              data.
            - Given a database connection failure (e.g. a locked file),
              when save_item() is called, then the transaction is rolled
              back, no partial row is written, and no id is returned.
        """
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO food_item
                    (inventory_id, name, food_type, quantity, price_per_unit, minimum_quantity)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    inventory_id,
                    item.name,
                    item.food_type,
                    item.quantity,
                    item.price_per_unit,
                    item.minimum_quantity,
                ),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_item(self, item_id: int) -> FoodItem | None:
        """Load a single FoodItem row by its primary key.

        Args:
            item_id (int): primary key of the FoodItem to load.

        Returns:
            FoodItem | None: the matching FoodItem instance, or None if
            no row with that ID exists.

        Test:
            - Given an item_id that exists, when get_item() is called,
              then the returned FoodItem's attributes match the stored
              row.
            - Given an item_id that does not exist, when get_item() is
              called, then None is returned instead of raising an
              unhandled exception.
        """
        row = self._connection.execute(
            "SELECT * FROM food_item WHERE food_id = ?", (item_id,)
        ).fetchone()
        return self._row_to_food_item(row) if row is not None else None

    def get_all_items(self) -> list[FoodItem]:
        """Load every stored FoodItem row.

        Returns:
            list[FoodItem]: all FoodItem instances currently persisted.

        Test:
            - Given 3 stored food items, when get_all_items() is called,
              then a list of length 3 is returned.
            - Given no stored food items, when get_all_items() is called,
              then an empty list is returned, not None.
        """
        rows = self._connection.execute("SELECT * FROM food_item").fetchall()
        return [self._row_to_food_item(row) for row in rows]

    def update_item(self, item: FoodItem) -> None:
        """Update an existing FoodItem row.

        Args:
            item (FoodItem): the FoodItem instance with updated attribute
                values (e.g. after decrease_quantity()).

        Test:
            - Given an existing FoodItem whose quantity changed, when
              update_item() is called, then get_item() returns the new
              value afterwards.
            - Given a FoodItem whose id does not exist in storage, when
              update_item() is called, then zero rows are affected and no
              exception is raised (no silent row creation, NFR-09).
        """
        try:
            self._connection.execute(
                """
                UPDATE food_item
                SET name = ?, food_type = ?, quantity = ?, price_per_unit = ?, minimum_quantity = ?
                WHERE food_id = ?
                """,
                (
                    item.name,
                    item.food_type,
                    item.quantity,
                    item.price_per_unit,
                    item.minimum_quantity,
                    item.id,
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def save_medication(self, medication: Medication, inventory_id: int) -> int:
        """Insert a new Medication row.

        Args:
            medication (Medication): the Medication instance to insert.
            inventory_id (int): id of the Inventory the medication belongs
                to.

        Returns:
            int: the medication_id assigned by SQLite (cursor.lastrowid).
            The caller is responsible for making the id available on its
            own Medication reference - this method does not assume
            `medication.id` is settable (Medication exposes `id` as a
            read-only property with no setter).

        Test:
            - Given a new, valid Medication and an existing inventory_id,
              when save_medication() is called, then the returned id is a
              positive int and get_medication() afterwards returns
              matching data.
            - Given a database connection failure (e.g. a locked file),
              when save_medication() is called, then the transaction is
              rolled back, no partial row is written, and no id is
              returned.
        """
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO medication (inventory_id, name, quantity, minimum_quantity)
                VALUES (?, ?, ?, ?)
                """,
                (inventory_id, medication.name, medication.quantity, medication.minimum_quantity),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_medication(self, medication_id: int) -> Medication | None:
        """Load a single Medication row by its primary key.

        Args:
            medication_id (int): primary key of the Medication to load.

        Returns:
            Medication | None: the matching Medication instance, or None
            if no row with that ID exists.

        Test:
            - Given a medication_id that exists, when get_medication() is
              called, then the returned Medication's attributes match the
              stored row.
            - Given a medication_id that does not exist, when
              get_medication() is called, then None is returned instead
              of raising an unhandled exception.
        """
        row = self._connection.execute(
            "SELECT * FROM medication WHERE medication_id = ?", (medication_id,)
        ).fetchone()
        return self._row_to_medication(row) if row is not None else None

    def get_all_medications(self) -> list[Medication]:
        """Load every stored Medication row.

        Returns:
            list[Medication]: all Medication instances currently
            persisted.

        Test:
            - Given 2 stored medications, when get_all_medications() is
              called, then a list of length 2 is returned.
            - Given no stored medications, when get_all_medications() is
              called, then an empty list is returned, not None.
        """
        rows = self._connection.execute("SELECT * FROM medication").fetchall()
        return [self._row_to_medication(row) for row in rows]

    def update_medication(self, medication: Medication) -> None:
        """Update an existing Medication row.

        Args:
            medication (Medication): the Medication instance with updated
                attribute values (e.g. after decrease_quantity()).

        Test:
            - Given an existing Medication whose quantity changed, when
              update_medication() is called, then get_medication()
              returns the new value afterwards.
            - Given a Medication whose id does not exist in storage, when
              update_medication() is called, then zero rows are affected
              and no exception is raised (no silent row creation,
              NFR-09).
        """
        try:
            self._connection.execute(
                "UPDATE medication SET name = ?, quantity = ?, minimum_quantity = ? WHERE medication_id = ?",
                (medication.name, medication.quantity, medication.minimum_quantity, medication.id),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def get_as_dataframe(self) -> pd.DataFrame:
        """Load all inventory stock (FoodItem and Medication) as one DataFrame.

        Used by ReportService to build the inventory report and export it
        as CSV/Excel. Combines both tables into one DataFrame with an
        `item_type` column distinguishing rows; food-only columns
        (food_type, price_per_unit) are None for Medication rows.

        Returns:
            pd.DataFrame: one row per FoodItem/Medication, columns per
            `_COMBINED_COLUMNS`.

        Test:
            - Given 3 stored food items and 2 stored medications, when
              get_as_dataframe() is called, then a DataFrame with 5 rows
              and the expected column names is returned.
            - Given an empty inventory, when get_as_dataframe() is called,
              then an empty DataFrame with the correct columns (not None)
              is returned, so ReportService can still export a valid
              empty report.
        """
        food_rows = self._connection.execute("SELECT * FROM food_item").fetchall()
        medication_rows = self._connection.execute("SELECT * FROM medication").fetchall()

        records = [
            {
                "id": row["food_id"],
                "item_type": "FoodItem",
                "name": row["name"],
                "food_type": row["food_type"],
                "quantity": row["quantity"],
                "price_per_unit": row["price_per_unit"],
                "minimum_quantity": row["minimum_quantity"],
            }
            for row in food_rows
        ] + [
            {
                "id": row["medication_id"],
                "item_type": "Medication",
                "name": row["name"],
                "food_type": None,
                "quantity": row["quantity"],
                "price_per_unit": None,
                "minimum_quantity": row["minimum_quantity"],
            }
            for row in medication_rows
        ]

        if not records:
            return pd.DataFrame(columns=list(_COMBINED_COLUMNS))
        return pd.DataFrame(records, columns=list(_COMBINED_COLUMNS))

    def _row_to_food_item(self, row: sqlite3.Row) -> FoodItem:
        """Build a FoodItem domain object from one `food_item` table row.

        Args:
            row (sqlite3.Row): one row from the `food_item` table
                (row_factory = sqlite3.Row, see
                SQLiteConnection.connect()).

        Returns:
            FoodItem: a FoodItem instance populated from the row.

        Test:
            - Given a row with all columns set, when _row_to_food_item()
              is called, then the returned FoodItem's attributes equal
              the row's values (row["food_id"] -> FoodItem.id, etc.).
            - Given a row where price_per_unit is NULL, when
              _row_to_food_item() is called, then
              FoodItem.price_per_unit is None instead of raising a
              conversion error.
        """
        from zoo_simulation.domain.food_item import FoodItem

        return FoodItem(
            id=row["food_id"],
            name=row["name"],
            food_type=row["food_type"],
            quantity=row["quantity"],
            price_per_unit=row["price_per_unit"],
            minimum_quantity=row["minimum_quantity"],
        )

    def _row_to_medication(self, row: sqlite3.Row) -> Medication:
        """Build a Medication domain object from one `medication` table row.

        Args:
            row (sqlite3.Row): one row from the `medication` table
                (row_factory = sqlite3.Row, see
                SQLiteConnection.connect()).

        Returns:
            Medication: a Medication instance populated from the row.

        Test:
            - Given a row with all columns set, when _row_to_medication()
              is called, then the returned Medication's attributes equal
              the row's values (row["medication_id"] -> Medication.id,
              etc.).
            - Given a row where minimum_quantity is NULL, when
              _row_to_medication() is called, then
              Medication.minimum_quantity is None instead of raising a
              conversion error.
        """
        from zoo_simulation.domain.medication import Medication

        return Medication(
            id=row["medication_id"],
            name=row["name"],
            quantity=row["quantity"],
            minimum_quantity=row["minimum_quantity"],
        )
