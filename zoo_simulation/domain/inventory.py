"""Inventory: manages food items and medication stock.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from zoo_simulation.domain.food_item import FoodItem
    from zoo_simulation.domain.medication import Medication

InventoryItem = Union["FoodItem", "Medication"]


class Inventory:
    """Inventory - the zoo's stock of FoodItem and Medication resources.

    Holds both resource kinds in a single collection rather than two
    separate lists: FoodItem and Medication both expose the same
    `id`/`increase_quantity()`/`decrease_quantity()`/`is_low_stock()`
    interface (duck typing), so `add_item()`/`remove_item()`/
    `consume_item()`/`get_low_stock_items()` work identically for either,
    matching aufgabe.md's description of Inventory managing "Futter...
    oder Medikamente" through one interface. Persistence still splits
    them into `food_item`/`medication` tables (see
    InventoryRepository.save_item()/save_medication()) - the caller
    persisting an Inventory is responsible for routing each item to the
    right repository method based on its type.

        - Constructor: stores all attributes privately.
        - _id (int | None): primary key once persisted, None for an
          Inventory that has not been saved yet.
        - _items (list[FoodItem | Medication]): all stocked resources,
          both kinds mixed together.
    """

    def __init__(self, id: int | None = None) -> None:
        """Create an empty Inventory.

        Args:
            id (int | None, optional): primary key if this Inventory was
                loaded from storage. Defaults to None for a new,
                not-yet-persisted Inventory.

        Test:
            - When the constructor is called, then `.items` is an empty
              list.
            - Given id=5, when the constructor is called, then `.id` is
              5.
        """
        self._id = id
        self._items: list[InventoryItem] = []

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def items(self) -> list[InventoryItem]:
        return list(self._items)

    def add_item(self, item: InventoryItem) -> None:
        """Add a FoodItem or Medication to the inventory.

        Args:
            item (FoodItem | Medication): the resource to add.

        Test:
            - Given an empty Inventory, when `add_item(food)` is called
              with a FoodItem, then `.items` contains exactly that item.
            - Given an Inventory with 2 items, when `add_item(medication)`
              is called with a Medication, then `.items` has 3 entries.
        """
        self._items.append(item)

    def remove_item(self, item_id: int) -> None:
        """Remove a resource by its ID, if present.

        Args:
            item_id (int): id of the FoodItem/Medication to remove.

        Test:
            - Given an Inventory containing an item with id=3, when
              `remove_item(3)` is called, then that item is no longer in
              `.items`.
            - Given an item_id not present in the Inventory, when
              `remove_item()` is called, then `.items` stays unchanged
              (no error raised).
        """
        self._items = [item for item in self._items if item.id != item_id]

    def consume_item(self, item_id: int, quantity: float) -> bool:
        """Consume some quantity of a stocked resource.

        Args:
            item_id (int): id of the FoodItem/Medication to consume from.
            quantity (float): amount to consume.

        Returns:
            bool: True if the item was found and had enough stock
                (delegates to the item's own `decrease_quantity()`),
                False if the item does not exist or stock was
                insufficient.

        Test:
            - Given a stocked FoodItem with id=1 and quantity=10.0, when
              `consume_item(1, 4.0)` is called, then it returns True and
              that item's quantity is 6.0.
            - Given an item_id not present in the Inventory, when
              `consume_item()` is called, then it returns False.
        """
        for item in self._items:
            if item.id == item_id:
                return item.decrease_quantity(quantity)
        return False

    def get_low_stock_items(self) -> list[InventoryItem]:
        """List every resource that has fallen to or below its minimum stock.

        Returns:
            list[FoodItem | Medication]: all items for which
            `is_low_stock()` is True.

        Test:
            - Given 3 stocked items where 1 is below its minimum
              quantity, when `get_low_stock_items()` is called, then a
              list of length 1 is returned.
            - Given no stocked items are low, when
              `get_low_stock_items()` is called, then an empty list is
              returned.
        """
        return [item for item in self._items if item.is_low_stock()]
