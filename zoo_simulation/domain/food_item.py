"""FoodItem: a consumable inventory item for feeding animals.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations


class FoodItem:
    """FoodItem - one type of food stocked in an Inventory.

        - Constructor: stores all attributes privately; `quantity` is the
          only attribute that changes after creation, and only through
          `increase_quantity()`/`decrease_quantity()` (never assigned
          directly), so Inventory can never push it into an inconsistent
          state (e.g. negative stock).
        - _id (int | None): primary key once persisted, None for a
          FoodItem that has not been saved yet.
        - _name (str): e.g. "Raw Meat".
        - _food_type (str): category, e.g. "meat", "hay", "fish".
        - _quantity (float): current stock, in whatever unit the food type
          is measured in (kg, pieces, ...).
        - _price_per_unit (float): cost per unit, used by FinanceManager
          when Zookeeper.feed_animal() records the resulting expense.
        - _minimum_quantity (float): stock threshold below which
          `is_low_stock()` reports True.
    """

    def __init__(
        self,
        name: str,
        food_type: str,
        quantity: float = 0.0,
        price_per_unit: float = 0.0,
        minimum_quantity: float = 0.0,
        id: int | None = None,
    ) -> None:
        """Create a FoodItem with the given attributes.

        Args:
            name (str): e.g. "Chicken".
            food_type (str): category, e.g. "meat", "hay", "fish".
            quantity (float, optional): starting stock. Defaults to 0.0.
            price_per_unit (float, optional): cost per unit. Defaults to
                0.0.
            minimum_quantity (float, optional): low-stock threshold.
                Defaults to 0.0.
            id (int | None, optional): primary key if this FoodItem was
                loaded from storage. Defaults to None for a new,
                not-yet-persisted FoodItem.

        Test:
            - Given name="Raw Meat" and quantity=10.0, when the
              constructor is called, then `.quantity` is 10.0 and `.name`
              is "Raw Meat".
            - Given no `id` is passed, when the constructor is called,
              then `.id` is None (new, not-yet-persisted FoodItem).
        """
        self._id = id
        self._name = name
        self._food_type = food_type
        self._quantity = quantity
        self._price_per_unit = price_per_unit
        self._minimum_quantity = minimum_quantity

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def food_type(self) -> str:
        return self._food_type

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def price_per_unit(self) -> float:
        return self._price_per_unit

    @property
    def minimum_quantity(self) -> float:
        return self._minimum_quantity

    def increase_quantity(self, amount: float) -> None:
        """Add stock, e.g. when a delivery arrives.

        Args:
            amount (float): amount to add. Must be positive; non-positive
                values are ignored (no-op), since a "negative delivery"
                is not a meaningful restock operation - see
                `decrease_quantity()` for reducing stock instead.

        Test:
            - Given quantity=10.0, when `increase_quantity(5.0)` is
              called, then `.quantity` is 15.0.
            - Given quantity=10.0, when `increase_quantity(-5.0)` is
              called, then `.quantity` stays 10.0 (ignored, not a valid
              restock amount).
        """
        if amount <= 0:
            return
        self._quantity += amount

    def decrease_quantity(self, amount: float) -> bool:
        """Consume stock, e.g. when Zookeeper.feed_animal() uses this food.

        Args:
            amount (float): amount to remove. Must be positive and not
                exceed the current stock.

        Returns:
            bool: True if the stock was sufficient and reduced
                accordingly, False if `amount` is non-positive or exceeds
                the current stock (in which case `.quantity` is left
                unchanged).

        Test:
            - Given quantity=10.0, when `decrease_quantity(4.0)` is
              called, then it returns True and `.quantity` is 6.0.
            - Given quantity=10.0, when `decrease_quantity(20.0)` is
              called, then it returns False and `.quantity` stays 10.0.
        """
        if amount <= 0 or amount > self._quantity:
            return False
        self._quantity -= amount
        return True

    def is_low_stock(self) -> bool:
        """Check whether stock has fallen to or below the minimum threshold.

        Returns:
            bool: True if `.quantity` is less than or equal to
                `.minimum_quantity`, False otherwise.

        Test:
            - Given quantity=2.0 and minimum_quantity=5.0, when
              `is_low_stock()` is called, then it returns True.
            - Given quantity=10.0 and minimum_quantity=5.0, when
              `is_low_stock()` is called, then it returns False.
        """
        return self._quantity <= self._minimum_quantity
