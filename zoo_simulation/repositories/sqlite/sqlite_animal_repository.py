"""sqlite_animal_repository.py - SQLite implementation of AnimalRepository.

    Implements AnimalRepository (repositories/interfaces/animal_repository.py)
    against the `animal` table defined in database/schema.sql, using a
    DatabaseConnection (SQLiteConnection in practice) for all SQL access.
    `animal` uses single-table inheritance (see schema.sql): the `species`
    column is the discriminator used to reconstruct the correct concrete
    subclass (Lion/Giraffe/Penguin) when reading a row back. Assumes each
    concrete Animal subclass's constructor accepts id/name/age/health/
    hunger/energy/food_preference as keyword arguments - species itself is
    implied by the chosen class, not passed explicitly. Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

import importlib
import sqlite3
from typing import TYPE_CHECKING

import pandas as pd

from zoo_simulation.repositories.interfaces.animal_repository import AnimalRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.animals.animal import Animal

_ANIMAL_COLUMNS = (
    "animal_id",
    "enclosure_id",
    "name",
    "species",
    "food_preference",
    "age",
    "health",
    "hunger",
    "energy",
)

_SPECIES_TO_CLASS = {
    "Lion": ("zoo_simulation.domain.animals.lion", "Lion"),
    "Giraffe": ("zoo_simulation.domain.animals.giraffe", "Giraffe"),
    "Penguin": ("zoo_simulation.domain.animals.penguin", "Penguin"),
}


class SQLAnimalRepository(AnimalRepository):
    """SQLAnimalRepository - persists Animal objects in the `animal` table.

        - Constructor: stores the DatabaseConnection used for all queries;
          does not open/close the connection itself (owned by the caller,
          e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `animal` table.
        - Module-level _SPECIES_TO_CLASS: maps the `species` discriminator
          column to the (module, class name) used to reconstruct the
          correct concrete Animal subclass when reading a row.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """Store the DatabaseConnection used for all Animal persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).

        Test:
            - Given a connected DatabaseConnection, when
              SQLAnimalRepository is constructed, then
              save()/get_by_id()/get_all()/update()/delete() can be called
              immediately without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection

    def save(self, animal: Animal, enclosure_id: int | None = None) -> int:
        """Insert a new Animal row.

        Args:
            animal (Animal): the Animal instance to insert (any concrete
                subclass: Lion, Giraffe, Penguin, ...).
            enclosure_id (int | None, optional): id of the Enclosure the
                animal is assigned to, or None if not yet assigned.
                Defaults to None.

        Returns:
            int: the animal_id assigned by SQLite (cursor.lastrowid). The
            caller is responsible for making the id available on its own
            Animal reference - this method does not assume `animal.id` is
            settable.

        Test:
            - Given a new, valid Animal object and an existing
              enclosure_id, when save() is called, then the returned id is
              a positive int and get_by_id(that id) afterwards returns
              matching data, including the enclosure assignment.
            - Given a database connection failure (e.g. a locked file),
              when save() is called, then the transaction is rolled back,
              no partial row is written, and no id is returned.
        """
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO animal
                    (enclosure_id, name, species, food_preference, age, health, hunger, energy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    enclosure_id,
                    animal.name,
                    animal.species,
                    getattr(animal, "food_preference", None),
                    animal.age,
                    animal.health,
                    animal.hunger,
                    animal.energy,
                ),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_by_id(self, animal_id: int) -> Animal | None:
        """Load a single Animal row by its primary key.

        Args:
            animal_id (int): primary key of the Animal to load.

        Returns:
            Animal | None: the matching Animal instance (as its correct
            concrete subclass), or None if no row with that ID exists.

        Test:
            - Given an animal_id that exists with species "Lion", when
              get_by_id() is called, then the returned object is a Lion
              instance whose attributes match the stored row.
            - Given an animal_id that does not exist, when get_by_id() is
              called, then None is returned instead of raising an
              unhandled exception.
        """
        row = self._connection.execute(
            "SELECT * FROM animal WHERE animal_id = ?", (animal_id,)
        ).fetchone()
        return self._row_to_animal(row) if row is not None else None

    def get_all(self) -> list[Animal]:
        """Load every stored Animal row.

        Returns:
            list[Animal]: all Animal instances currently persisted, each
            as its correct concrete subclass.

        Test:
            - Given 3 stored animals of different species, when get_all()
              is called, then a list of length 3 is returned with each
              entry as its correct concrete subclass.
            - Given no stored animals, when get_all() is called, then an
              empty list is returned, not None.
        """
        rows = self._connection.execute("SELECT * FROM animal").fetchall()
        return [self._row_to_animal(row) for row in rows]

    def update(self, animal: Animal, enclosure_id: int | None = None) -> None:
        """Update an existing Animal row.

        Args:
            animal (Animal): the Animal instance with updated attribute
                values (e.g. after eat()/sleep()/grow_older()).
            enclosure_id (int | None, optional): id of the Enclosure the
                animal is now assigned to. Defaults to None, meaning
                "leave the current assignment unchanged" (implemented via
                SQL COALESCE), not "unassign".

        Test:
            - Given an existing Animal whose hunger changed, when
              update() is called without enclosure_id, then get_by_id()
              returns the new hunger value afterwards and the enclosure
              assignment is unchanged.
            - Given an Animal whose id does not exist in storage, when
              update() is called, then zero rows are affected and no
              exception is raised (no silent row creation, NFR-09).
        """
        try:
            self._connection.execute(
                """
                UPDATE animal
                SET enclosure_id = COALESCE(?, enclosure_id),
                    name = ?,
                    food_preference = ?,
                    age = ?,
                    health = ?,
                    hunger = ?,
                    energy = ?
                WHERE animal_id = ?
                """,
                (
                    enclosure_id,
                    animal.name,
                    getattr(animal, "food_preference", None),
                    animal.age,
                    animal.health,
                    animal.hunger,
                    animal.energy,
                    animal.id,
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def delete(self, animal_id: int) -> None:
        """Remove an Animal row from storage.

        Args:
            animal_id (int): primary key of the Animal to delete.

        Test:
            - Given an animal_id that exists, when delete() is called,
              then a subsequent get_by_id() for that id returns None.
            - Given an animal_id that does not exist, when delete() is
              called, then no exception is raised (0 rows affected,
              no-op instead of crash).
        """
        try:
            self._connection.execute(
                "DELETE FROM animal WHERE animal_id = ?", (animal_id,)
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def get_as_dataframe(self) -> pd.DataFrame:
        """Load every stored Animal row as a pandas DataFrame.

        Used by ReportService to build the animal report and export it as
        CSV/Excel. Unlike get_all()/get_by_id(), this returns raw column
        data (not reconstructed Animal objects), since a report only needs
        tabular data.

        Returns:
            pd.DataFrame: one row per Animal, columns matching the
            `animal` table.

        Test:
            - Given 3 stored animals, when get_as_dataframe() is called,
              then a DataFrame with 3 rows and the expected column names
              is returned.
            - Given no stored animals, when get_as_dataframe() is called,
              then an empty DataFrame with the correct columns (not None)
              is returned, so ReportService can still export a valid
              empty report.
        """
        rows = self._connection.execute("SELECT * FROM animal").fetchall()
        if not rows:
            return pd.DataFrame(columns=_ANIMAL_COLUMNS)
        return pd.DataFrame([dict(row) for row in rows], columns=list(_ANIMAL_COLUMNS))

    def _row_to_animal(self, row: sqlite3.Row) -> Animal:
        """Build the correct concrete Animal subclass from one `animal` row.

        Args:
            row (sqlite3.Row): one row from the `animal` table (row_factory
                = sqlite3.Row, see SQLiteConnection.connect()).

        Returns:
            Animal: a Lion/Giraffe/Penguin instance populated from the
            row, chosen via the `species` discriminator column.

        Test:
            - Given a row with species="Giraffe", when _row_to_animal()
              is called, then a Giraffe instance is returned with
              attributes equal to the row's values.
            - Given a row with a species value not present in
              _SPECIES_TO_CLASS (e.g. corrupted data), when
              _row_to_animal() is called, then a ValueError is raised
              instead of silently returning a wrong/generic object.
        """
        species = row["species"]
        if species not in _SPECIES_TO_CLASS:
            raise ValueError(f"Unknown animal species stored in database: {species!r}")

        module_path, class_name = _SPECIES_TO_CLASS[species]
        animal_class = getattr(importlib.import_module(module_path), class_name)

        return animal_class(
            id=row["animal_id"],
            name=row["name"],
            food_preference=row["food_preference"],
            age=row["age"],
            health=row["health"],
            hunger=row["hunger"],
            energy=row["energy"],
        )
