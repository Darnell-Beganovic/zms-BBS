"""employee_repository.py - repository interface for persisting Employee objects.

    Defines the contract the Backend focus (Darnell) programs against to
    persist/read Employee objects (Zookeeper, Veterinarian, Administrator,
    ...), without depending on a concrete database technology (Dependency
    Inversion Principle). The only implementation planned is
    SQLEmployeeRepository
    (repositories/sqlite/sqlite_employee_repository.py). Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.domain.employees.employee import Employee


class EmployeeRepository(ABC):
    """EmployeeRepository - abstract interface for Employee persistence.

        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete implementations own their own
          DatabaseConnection.
    """

    @abstractmethod
    def save(self, employee: Employee, zoo_id: int) -> int:
        """Persist a new Employee.

        Args:
            employee (Employee): the Employee instance to insert (any
                concrete subclass: Zookeeper, Veterinarian, Administrator,
                ...).
            zoo_id (int): id of the Zoo the employee belongs to. Employee
                carries no zoo_id attribute (see the class diagram), so it
                is supplied separately, mirroring how AnimalRepository
                takes enclosure_id and EnclosureRepository takes zoo_id.

        Returns:
            int: the employee_id assigned by the database (e.g. read back
            via cursor.lastrowid after the INSERT). Implementations must
            NOT assume the passed-in `employee` instance's `id` is
            settable (Backend domain objects such as Transaction expose
            `id` as a read-only property with no setter) - the caller is
            responsible for making the returned id available on its own
            reference.

        Test:
            - Any implementation, given a new, valid Employee object, when
              save() is called, must return the new employee_id, and that
              id must be retrievable via get_by_id() afterwards with
              matching data.
            - Any implementation, given an Employee with an id that
              already exists, when save() is called, must not silently
              create a conflicting duplicate row (update() exists
              separately for modifying an existing Employee).
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, employee_id: int) -> Employee | None:
        """Retrieve an Employee by its ID.

        Args:
            employee_id (int): primary key of the Employee to load.

        Returns:
            Employee | None: the matching Employee instance, or None if
            no Employee with that ID exists.

        Test:
            - Any implementation, given an employee_id that exists, when
              get_by_id() is called, must return an Employee whose
              attributes match the stored row (including its concrete
              type, e.g. Veterinarian).
            - Any implementation, given an employee_id that does not
              exist, when get_by_id() is called, must return None instead
              of raising an unhandled exception.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Employee]:
        """Retrieve every stored Employee.

        Returns:
            list[Employee]: all Employee instances currently persisted,
            regardless of concrete subclass.

        Test:
            - Any implementation, given 3 stored employees of different
              roles, when get_all() is called, must return a list of
              length 3 with each entry as its correct concrete subclass.
            - Any implementation, given no stored employees, when
              get_all() is called, must return an empty list, not None.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, employee: Employee) -> None:
        """Persist changes to an existing Employee.

        Args:
            employee (Employee): the Employee instance with updated
                attribute values (e.g. after a salary change).

        Test:
            - Any implementation, given an existing Employee whose salary
              changed, when update() is called, must make get_by_id()
              return the new value afterwards.
            - Any implementation, given an Employee whose id does not
              exist in storage, when update() is called, must not
              silently create a new row and must not corrupt existing
              data (NFR-09).
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, employee_id: int) -> None:
        """Remove an Employee from storage.

        Args:
            employee_id (int): primary key of the Employee to delete.

        Test:
            - Any implementation, given an employee_id that exists, when
              delete() is called, must make a subsequent get_by_id() for
              that id return None.
            - Any implementation, given an employee_id that does not
              exist, when delete() is called, must not raise an unhandled
              exception (no-op instead of crash).
        """
        raise NotImplementedError
