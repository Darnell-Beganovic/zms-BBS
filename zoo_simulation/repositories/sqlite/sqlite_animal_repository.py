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

    Fixed 2026-08-09: `_row_to_animal()` previously called the Animal
    subclass constructors without `behaviors`, a required positional
    argument (`Animal *-- "1..*" Behavior`, see Klassendiagramm_Code.md) -
    every `get_by_id()`/`get_all()` call raised `TypeError` immediately.
    `Behavior` objects are not persisted anywhere (no `behavior` table in
    schema.sql - they carry no id/state worth round-tripping, see
    domain/behaviors/*.py), so there is nothing to load back; instead,
    reconstructed animals are given a fixed default Behavior set built from
    the stored `food_preference` (see `_default_behaviors()`). This
    satisfies the 1..* composition constraint but is a deliberate,
    documented approximation, not a restoration of whatever Behaviors the
    animal had before saving - see planning_db_kaiss.md section 6.
"""

from __future__ import annotations

import importlib
import sqlite3
from typing import TYPE_CHECKING

import pandas as pd

from zoo_simulation.domain.behaviors.feeding_behavior import FeedingBehavior
from zoo_simulation.domain.behaviors.rest_behavior import RestBehavior
from zoo_simulation.domain.behaviors.social_behavior import SocialBehavior
from zoo_simulation.repositories.interfaces.animal_repository import AnimalRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.animals.animal import Animal
    from zoo_simulation.domain.behaviors.behavior import Behavior

# Vorbelegung fuer neu geladene Tiere - siehe Modul-Docstring ("Fixed
# 2026-08-09"): moderates Fressverhalten, Ruheverhalten und ein neutrales
# Sozialverhalten, unabhaengig von Spezies. Werte bewusst schlicht gehalten
# (kein Anspruch, den exakten Zustand vor dem letzten Speichern zu treffen).
# Gesenkt von 20/50 auf 1/10 (Darnell Beganovic, Backend-Schwerpunkt,
# 2026-08-09, siehe planning_backend_darnell.md Abschnitt 2.11 und
# planning_db_kaiss.md Abschnitt 6): SimulationEngine.update_animals()
# ruft jetzt zusaetzlich Animal.move()/sleep() pro Tick auf. Bei den
# urspruenglichen Werten (20/50) ueberstieg RestBehavior+SocialBehaviors
# passive Erholung (+20 bzw. +5 Energie/Tick) jeden Energieverlust durch
# Bewegung (3-5 je nach Spezies) bei weitem, sodass Energie immer gegen
# 100 konvergierte und nie unter die Schlaf-Schwelle sank - auch bei
# einem gesenkten RestBehavior allein blieb SocialBehaviors eigener
# Beitrag (+5) noch zu hoch. Bei 1/10 betraegt die kombinierte passive
# Erholung nur noch +2 Energie/Tick, weniger als der Bewegungsaufwand
# jeder Spezies (Giraffe am niedrigsten mit 3) - Energie sinkt jetzt
# unter normalen Bedingungen jeden Tick tatsaechlich, bis `sleep()` sie
# wieder deutlich anhebt.
_DEFAULT_REST_DURATION = 1
_DEFAULT_SOCIAL_LEVEL = 10

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

    def _default_behaviors(self, food_preference: str | None) -> list[Behavior]:
        """Build the default Behavior set assigned to every reconstructed Animal.

        See the module docstring ("Fixed 2026-08-09") for why this exists:
        Behavior objects are not persisted, so there is nothing to load -
        this fabricates a fixed, reasonable set instead, satisfying
        `Animal`'s `1..*` Behavior composition requirement.

        Args:
            food_preference (str | None): the animal's stored
                `food_preference` column value, passed straight into the
                `FeedingBehavior` (falls back to `""` if `NULL`, matching
                `FeedingBehavior.__init__()`'s own lack of validation for
                an empty preference).

        Returns:
            list[Behavior]: `[FeedingBehavior(food_preference),
            RestBehavior(_DEFAULT_REST_DURATION),
            SocialBehavior(_DEFAULT_SOCIAL_LEVEL)]` - always non-empty.

        Test:
            - Given food_preference="meat", when
              `_default_behaviors("meat")` is called, then the returned
              list has length 3 and its `FeedingBehavior` entry has
              `.food_preference == "meat"`.
            - Given food_preference=None (NULL column), when
              `_default_behaviors(None)` is called, then no exception is
              raised and the `FeedingBehavior` entry's `.food_preference`
              is `""`.
        """
        return [
            FeedingBehavior(food_preference or ""),
            RestBehavior(_DEFAULT_REST_DURATION),
            SocialBehavior(_DEFAULT_SOCIAL_LEVEL),
        ]

    def _row_to_animal(self, row: sqlite3.Row) -> Animal:
        """Build the correct concrete Animal subclass from one `animal` row.

        Args:
            row (sqlite3.Row): one row from the `animal` table (row_factory
                = sqlite3.Row, see SQLiteConnection.connect()).

        Returns:
            Animal: a Lion/Giraffe/Penguin instance populated from the
            row, chosen via the `species` discriminator column, with a
            default Behavior set (see `_default_behaviors()`).

        Test:
            - Given a row with species="Giraffe", when _row_to_animal()
              is called, then a Giraffe instance is returned with
              attributes equal to the row's values and a non-empty
              `.behaviors` list (constructor would otherwise raise
              ValueError per Animal's 1..* composition requirement).
            - Given a row with a species value not present in
              _SPECIES_TO_CLASS (e.g. corrupted data), when
              _row_to_animal() is called, then a ValueError is raised
              instead of silently returning a wrong/generic object.
            - Given a row where age/health/hunger/energy are NULL
              (schema.sql allows it - no NOT NULL constraint), when
              _row_to_animal() is called, then Animal's own constructor
              defaults are used instead of raising TypeError.
        """
        species = row["species"]
        if species not in _SPECIES_TO_CLASS:
            raise ValueError(f"Unknown animal species stored in database: {species!r}")

        module_path, class_name = _SPECIES_TO_CLASS[species]
        animal_class = getattr(importlib.import_module(module_path), class_name)

        kwargs = {
            "id": row["animal_id"],
            "name": row["name"],
            "food_preference": row["food_preference"],
            "behaviors": self._default_behaviors(row["food_preference"]),
        }
        for stat in ("age", "health", "hunger", "energy"):
            if row[stat] is not None:
                kwargs[stat] = row[stat]

        return animal_class(**kwargs)
