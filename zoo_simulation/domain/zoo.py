"""Zoo: the central aggregate root of the zoo management system.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.domain.employees.employee import Employee
    from zoo_simulation.domain.enclosure import Enclosure
    from zoo_simulation.domain.finance_manager import FinanceManager
    from zoo_simulation.domain.inventory import Inventory


class Zoo:
    """Zoo - the central aggregate representing the whole zoo.

    Composed of 1..* Enclosure (`Zoo *-- "1..*" Enclosure`), exactly one
    Inventory and one FinanceManager (`Zoo *-- "1" ...` each), and
    aggregates 0..* Employee (`Zoo o-- "0..*" Employee`) - matching the
    class diagram exactly.

        - Constructor: stores all attributes privately; `current_visitors`
          only changes through `register_visitor()`, never assigned
          directly.
        - _id (int | None): primary key once persisted, None for a Zoo
          that has not been saved yet.
        - _name (str): e.g. "Berlin Zoo".
        - _location (str): e.g. "Berlin, Germany".
        - _current_visitors (int): visitors currently on-site.
        - _maximum_visitors (int): capacity limit.
        - _enclosures (list[Enclosure]): at least one, enforced in the
          constructor (1..* composition).
        - _employees (list[Employee]): zero or more (0..* aggregation).
        - _inventory (Inventory): the zoo's single Inventory.
        - _finance_manager (FinanceManager): the zoo's single
          FinanceManager.
    """

    def __init__(
        self,
        name: str,
        location: str,
        maximum_visitors: int,
        enclosures: list[Enclosure],
        inventory: Inventory,
        finance_manager: FinanceManager,
        employees: list[Employee] | None = None,
        current_visitors: int = 0,
        id: int | None = None,
    ) -> None:
        """Create a Zoo with the given attributes.

        Args:
            name (str): e.g. "Berlin Zoo".
            location (str): e.g. "Berlin, Germany".
            maximum_visitors (int): visitor capacity.
            enclosures (list[Enclosure]): at least one enclosure this
                zoo owns. Raises ValueError if empty, since the class
                diagram's `1..*` multiplicity requires at least one.
            inventory (Inventory): the zoo's single Inventory.
            finance_manager (FinanceManager): the zoo's single
                FinanceManager.
            employees (list[Employee] | None, optional): employees this
                zoo employs. Defaults to None (empty list) - a brand-new
                zoo may not have hired anyone yet (0..* aggregation).
            current_visitors (int, optional): visitors currently on-site.
                Defaults to 0.
            id (int | None, optional): primary key if loaded from
                storage. Defaults to None.

        Raises:
            ValueError: if `enclosures` is empty.

        Test:
            - Given name="Berlin Zoo" and a non-empty enclosures list,
              when the constructor is called, then `.name` is "Berlin
              Zoo" and `.employees` is an empty list (default).
            - Given an empty `enclosures` list, when the constructor is
              called, then a ValueError is raised.
        """
        if not enclosures:
            raise ValueError("Zoo requires at least one Enclosure (1..* composition).")
        self._id = id
        self._name = name
        self._location = location
        self._maximum_visitors = maximum_visitors
        self._current_visitors = current_visitors
        self._enclosures = list(enclosures)
        self._employees: list[Employee] = list(employees) if employees else []
        self._inventory = inventory
        self._finance_manager = finance_manager

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def location(self) -> str:
        return self._location

    @property
    def current_visitors(self) -> int:
        return self._current_visitors

    @property
    def maximum_visitors(self) -> int:
        return self._maximum_visitors

    @property
    def enclosures(self) -> list[Enclosure]:
        return list(self._enclosures)

    @property
    def employees(self) -> list[Employee]:
        return list(self._employees)

    @property
    def inventory(self) -> Inventory:
        return self._inventory

    @property
    def finance_manager(self) -> FinanceManager:
        return self._finance_manager

    def add_enclosure(self, enclosure: Enclosure) -> None:
        """Add an enclosure to this zoo.

        Args:
            enclosure (Enclosure): the enclosure to add.

        Test:
            - Given a Zoo with 1 enclosure, when `add_enclosure()` is
              called, then `.enclosures` has 2 entries.
            - Given a newly added Enclosure, when `add_enclosure()` is
              called, then that exact instance is present in
              `.enclosures` afterwards.
        """
        self._enclosures.append(enclosure)

    def add_employee(self, employee: Employee) -> None:
        """Add an employee to this zoo.

        Args:
            employee (Employee): the employee to add.

        Test:
            - Given a Zoo with no employees, when `add_employee()` is
              called, then `.employees` has 1 entry.
            - Given an already-employed Employee instance, when
              `add_employee()` is called again with it, then
              `.employees` contains it twice (no duplicate check - hiring
              the same person twice is a caller error, not validated
              here).
        """
        self._employees.append(employee)

    def register_visitor(self) -> bool:
        """Admit one visitor, if the zoo has not reached capacity.

        Returns:
            bool: True and increments `current_visitors` if there is
                room, False (no change) if the zoo is at
                `maximum_visitors`.

        Test:
            - Given current_visitors=5 and maximum_visitors=10, when
              `register_visitor()` is called, then it returns True and
              `.current_visitors` is 6.
            - Given current_visitors == maximum_visitors, when
              `register_visitor()` is called, then it returns False and
              `.current_visitors` stays unchanged.
        """
        if self._current_visitors >= self._maximum_visitors:
            return False
        self._current_visitors += 1
        return True

    def calculate_average_welfare(self) -> float:
        """Compute the average welfare across every housed animal.

        Returns:
            float: the mean of `Animal.calculate_welfare()` over all
                animals in all enclosures, or 0.0 if the zoo currently
                houses no animals (avoids a division by zero).

        Test:
            - Given 2 enclosures with animals whose welfare scores are
              80.0 and 100.0, when `calculate_average_welfare()` is
              called, then it returns 90.0.
            - Given no enclosure houses any animal, when
              `calculate_average_welfare()` is called, then it returns
              0.0 instead of raising a division-by-zero error.
        """
        animals = [animal for enclosure in self._enclosures for animal in enclosure.animals]
        if not animals:
            return 0.0
        return sum(animal.calculate_welfare() for animal in animals) / len(animals)
