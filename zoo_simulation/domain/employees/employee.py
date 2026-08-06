"""Abstract base class for all zoo employees.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from abc import ABC, abstractmethod

_WORKING_DAYS_PER_MONTH = 30


class Employee(ABC):
    """Employee - abstract base class for every zoo employee type.

        - Constructor: stores all attributes privately; there are no
          setters - a raise/promotion is modeled as hiring a new
          Employee record via EmployeeRepository, not as mutating an
          existing one, mirroring Transaction's immutability convention.
        - _id (int | None): primary key once persisted, None for an
          Employee that has not been saved yet.
        - _name (str): e.g. "Alex Meier".
        - _salary (float): monthly salary, used by
          `calculate_daily_salary()`.
    """

    def __init__(
        self,
        name: str,
        salary: float = 0.0,
        id: int | None = None,
    ) -> None:
        """Create an Employee with the given attributes.

        Args:
            name (str): e.g. "Alex Meier".
            salary (float, optional): monthly salary. Defaults to 0.0.
            id (int | None, optional): primary key if this Employee was
                loaded from storage. Defaults to None for a new,
                not-yet-persisted Employee.

        Test:
            - Given name="Alex Meier" and salary=3000.0, when the
              constructor is called, then `.name` is "Alex Meier" and
              `.salary` is 3000.0.
            - Given no `id` is passed, when the constructor is called,
              then `.id` is None (new, not-yet-persisted Employee).
        """
        self._id = id
        self._name = name
        self._salary = salary

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def salary(self) -> float:
        return self._salary

    def calculate_daily_salary(self) -> float:
        """Compute the daily portion of this employee's monthly salary.

        Assumes a fixed 30-day month (no calendar-specific day counts,
        weekends or holidays - out of scope for this simulation's level
        of detail).

        Returns:
            float: `salary / 30`.

        Test:
            - Given salary=3000.0, when `calculate_daily_salary()` is
              called, then it returns 100.0.
            - Given salary=0.0, when `calculate_daily_salary()` is
              called, then it returns 0.0.
        """
        return self._salary / _WORKING_DAYS_PER_MONTH

    @abstractmethod
    def perform_task(self) -> str:
        """Perform this employee's characteristic daily task. Role-specific.

        Returns:
            str: a human-readable description of the task performed.

        Test:
            - See concrete subclasses (Zookeeper, Veterinarian,
              Administrator) for concrete Given/When/Then cases.
        """
        raise NotImplementedError
