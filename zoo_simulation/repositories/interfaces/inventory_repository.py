"""inventory_repository.py - repository interface for persisting FoodItem and Medication objects.

    Defines the contract the Backend focus (Darnell) programs against to
    persist/read the two kinds of inventory stock (FoodItem, Medication),
    without depending on a concrete database technology (Dependency
    Inversion Principle). FoodItem and Medication get parallel method sets
    because Inventory composes them as two separate collections in the
    class diagram (Inventory *-- FoodItem, Inventory *-- Medication) and
    they live in two separate tables (food_item, medication). The only
    implementation planned is SQLInventoryRepository
    (repositories/sqlite/sqlite_inventory_repository.py). Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

    Added 2026-08-09: `get_inventory(zoo_id)` reconstructs the actual
    `Inventory` aggregate (not just its items) - needed so
    `ZooRepository` can build a complete `Zoo` object (`Zoo *-- "1"
    Inventory`), which its constructor requires. Previously this
    interface only exposed FoodItem/Medication item access, with no way
    to obtain an `Inventory` instance itself; see
    planning_db_kaiss.md section 6 for the full rationale.

    Added 2026-08-09 (Darnell Beganovic, Backend focus, while wiring the
    application entry point): `create_inventory(zoo_id)` - there was no
    way to create the `inventory` table's row itself (`save_item()`/
    `save_medication()` both require an already-existing `inventory_id`,
    and no method inserted one). A brand-new Zoo has no FoodItem/
    Medication rows to save yet, so nothing could ever create its
    `inventory` row in the first place.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from zoo_simulation.domain.food_item import FoodItem
    from zoo_simulation.domain.inventory import Inventory
    from zoo_simulation.domain.medication import Medication


class InventoryRepository(ABC):
    """InventoryRepository - abstract interface for FoodItem/Medication persistence.

        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete implementations own their own
          DatabaseConnection.
    """

    @abstractmethod
    def save_item(self, item: FoodItem, inventory_id: int) -> int:
        """Persist a new FoodItem.

        Args:
            item (FoodItem): the FoodItem instance to insert.
            inventory_id (int): id of the Inventory the item belongs to.
                FoodItem carries no inventory_id attribute (see the class
                diagram), so it is supplied separately, mirroring how
                AnimalRepository takes enclosure_id and EnclosureRepository
                takes zoo_id.

        Returns:
            int: the food_id assigned by the database (e.g. read back via
            cursor.lastrowid after the INSERT). Implementations must NOT
            assume the passed-in `item` instance's `id` is settable
            (FoodItem exposes `id` as a read-only property with no
            setter) - the caller is responsible for making the returned
            id available on its own reference.

        Test:
            - Any implementation, given a new, valid FoodItem and an
              existing inventory_id, when save_item() is called, must
              return the new food_id, and it must be retrievable via
              get_item() afterwards with matching data.
            - Any implementation, given a FoodItem with an id that already
              exists, when save_item() is called, must not silently
              create a conflicting duplicate row (update_item() exists
              separately for modifying an existing FoodItem).
        """
        raise NotImplementedError

    @abstractmethod
    def get_item(self, item_id: int) -> FoodItem | None:
        """Retrieve a FoodItem by its ID.

        Args:
            item_id (int): primary key of the FoodItem to load.

        Returns:
            FoodItem | None: the matching FoodItem instance, or None if
            no FoodItem with that ID exists.

        Test:
            - Any implementation, given an item_id that exists, when
              get_item() is called, must return a FoodItem whose
              attributes match the stored row.
            - Any implementation, given an item_id that does not exist,
              when get_item() is called, must return None instead of
              raising an unhandled exception.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_items(self) -> list[FoodItem]:
        """Retrieve every stored FoodItem.

        Returns:
            list[FoodItem]: all FoodItem instances currently persisted.

        Test:
            - Any implementation, given 3 stored food items, when
              get_all_items() is called, must return a list of length 3.
            - Any implementation, given no stored food items, when
              get_all_items() is called, must return an empty list, not
              None.
        """
        raise NotImplementedError

    @abstractmethod
    def update_item(self, item: FoodItem) -> None:
        """Persist changes to an existing FoodItem.

        Args:
            item (FoodItem): the FoodItem instance with updated attribute
                values (e.g. after decrease_quantity()/increase_quantity()).

        Test:
            - Any implementation, given an existing FoodItem whose
              quantity changed, when update_item() is called, must make
              get_item() return the new value afterwards.
            - Any implementation, given a FoodItem whose id does not exist
              in storage, when update_item() is called, must not silently
              create a new row and must not corrupt existing data
              (NFR-09).
        """
        raise NotImplementedError

    @abstractmethod
    def save_medication(self, medication: Medication, inventory_id: int) -> int:
        """Persist a new Medication.

        Args:
            medication (Medication): the Medication instance to insert.
            inventory_id (int): id of the Inventory the medication belongs
                to. Medication carries no inventory_id attribute (see the
                class diagram), so it is supplied separately, the same
                way save_item() takes it for FoodItem.

        Returns:
            int: the medication_id assigned by the database (e.g. read
            back via cursor.lastrowid after the INSERT). Implementations
            must NOT assume the passed-in `medication` instance's `id` is
            settable (Medication exposes `id` as a read-only property
            with no setter) - the caller is responsible for making the
            returned id available on its own reference.

        Test:
            - Any implementation, given a new, valid Medication, when
              save_medication() is called, must return the new
              medication_id, and it must be retrievable via
              get_medication() afterwards with matching data.
            - Any implementation, given a Medication with an id that
              already exists, when save_medication() is called, must not
              silently create a conflicting duplicate row
              (update_medication() exists separately for modifying an
              existing Medication).
        """
        raise NotImplementedError

    @abstractmethod
    def get_medication(self, medication_id: int) -> Medication | None:
        """Retrieve a Medication by its ID.

        Args:
            medication_id (int): primary key of the Medication to load.

        Returns:
            Medication | None: the matching Medication instance, or None
            if no Medication with that ID exists.

        Test:
            - Any implementation, given a medication_id that exists, when
              get_medication() is called, must return a Medication whose
              attributes match the stored row.
            - Any implementation, given a medication_id that does not
              exist, when get_medication() is called, must return None
              instead of raising an unhandled exception.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_medications(self) -> list[Medication]:
        """Retrieve every stored Medication.

        Returns:
            list[Medication]: all Medication instances currently
            persisted.

        Test:
            - Any implementation, given 2 stored medications, when
              get_all_medications() is called, must return a list of
              length 2.
            - Any implementation, given no stored medications, when
              get_all_medications() is called, must return an empty list,
              not None.
        """
        raise NotImplementedError

    @abstractmethod
    def update_medication(self, medication: Medication) -> None:
        """Persist changes to an existing Medication.

        Args:
            medication (Medication): the Medication instance with updated
                attribute values (e.g. after decrease_quantity()).

        Test:
            - Any implementation, given an existing Medication whose
              quantity changed, when update_medication() is called, must
              make get_medication() return the new value afterwards.
            - Any implementation, given a Medication whose id does not
              exist in storage, when update_medication() is called, must
              not silently create a new row and must not corrupt existing
              data (NFR-09).
        """
        raise NotImplementedError

    @abstractmethod
    def get_as_dataframe(self) -> pd.DataFrame:
        """Retrieve all inventory stock (FoodItem and Medication) as one DataFrame.

        Used by ReportService to build the inventory report and export it
        as CSV/Excel. Combines both kinds of stock into a single table so
        the report shows the whole inventory at a glance.

        Returns:
            pd.DataFrame: one row per FoodItem/Medication, with a column
            identifying which kind of item each row is.

        Test:
            - Any implementation, given 3 stored food items and 2 stored
              medications, when get_as_dataframe() is called, must return
              a DataFrame with 5 rows and the expected column names.
            - Any implementation, given an empty inventory, when
              get_as_dataframe() is called, must return an empty
              DataFrame with the correct columns (not None), so
              ReportService can still export a valid empty report.
        """
        raise NotImplementedError

    @abstractmethod
    def get_inventory(self, zoo_id: int) -> Inventory | None:
        """Reconstruct the full Inventory aggregate (with all its items) for a zoo.

        Added 2026-08-09 (see module docstring) so `ZooRepository` can
        build a complete `Zoo` object - `Inventory` is a required
        constructor argument (`Zoo *-- "1" Inventory`), and this was the
        only way to obtain a populated `Inventory` instance rather than
        just its individual FoodItem/Medication rows.

        Args:
            zoo_id (int): id of the Zoo whose Inventory should be loaded
                (the `inventory` table has a unique `zoo_id` column, so
                there is exactly zero or one Inventory per zoo).

        Returns:
            Inventory | None: an `Inventory` instance with every stored
            FoodItem/Medication already added via `add_item()`, or `None`
            if this zoo has no `inventory` row yet.

        Test:
            - Given a zoo whose inventory has 2 food items and 1
              medication, when `get_inventory(zoo_id)` is called, then the
              returned `Inventory.items` has length 3.
            - Given a `zoo_id` with no matching `inventory` row, when
              `get_inventory(zoo_id)` is called, then `None` is returned
              instead of raising an unhandled exception.
        """
        raise NotImplementedError

    @abstractmethod
    def create_inventory(self, zoo_id: int) -> int:
        """Create the (empty) `inventory` row for a zoo that does not have one yet.

        Args:
            zoo_id (int): id of the Zoo to create an Inventory for. The
                `inventory` table's `zoo_id` column is unique, so calling
                this twice for the same zoo_id must fail rather than
                create a second row.

        Returns:
            int: the `inventory_id` assigned by the database
            (`cursor.lastrowid`), for use as `save_item()`/
            `save_medication()`'s `inventory_id` argument.

        Test:
            - Given a zoo_id with no existing `inventory` row, when
              `create_inventory(zoo_id)` is called, then it returns a
              positive int and `get_inventory(zoo_id)` afterwards returns
              an empty `Inventory` instead of `None`.
            - Given a zoo_id that already has an `inventory` row, when
              `create_inventory(zoo_id)` is called again, then it raises
              an error (e.g. a uniqueness-constraint violation) instead
              of silently creating a second row for the same zoo.
        """
        raise NotImplementedError
