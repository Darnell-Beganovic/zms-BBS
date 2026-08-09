"""sqlite_employee_repository.py - SQLite implementation of EmployeeRepository.

    Implements EmployeeRepository
    (repositories/interfaces/employee_repository.py) against the
    `employee` table defined in database/schema.sql. `employee` uses
    single-table inheritance (see schema.sql): the `employee_type` column
    is the discriminator used to reconstruct the correct concrete subclass
    (Zookeeper/Veterinarian/Administrator) when reading a row back.
    Assumes each concrete Employee subclass's constructor accepts id/name/
    salary as keyword arguments - employee_type itself is implied by the
    chosen class, not passed explicitly. Schwerpunkt: Datenbank - Kaiss
    Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

    Fixed 2026-08-09: `_row_to_employee()` previously called every
    Employee subclass constructor with only id/name/salary - fine for
    Zookeeper/Veterinarian (no extra required arguments), but
    `Administrator` also requires `finance_manager` (a
    `FinanceManager`, constructor-injected per
    planning_backend_darnell.md section 2.3), so every `Administrator`
    row raised `TypeError` on load. `SQLEmployeeRepository` now takes a
    `FinanceRepository` dependency (same pattern as
    `SQLZooRepository`, see that module's docstring) and builds a fresh
    `FinanceManager(balance=...)` for reconstructed Administrators only.
    This is a fresh FinanceManager reflecting the current balance, not
    literally the same Python object as any other loaded Zoo's
    FinanceManager - FinanceManager has no persisted identity of its own
    (no table, no id) for this repository to match it up by; see
    planning_db_kaiss.md section 6.
"""

from __future__ import annotations

import importlib
import sqlite3
from typing import TYPE_CHECKING

from zoo_simulation.domain.finance_manager import FinanceManager
from zoo_simulation.repositories.interfaces.employee_repository import EmployeeRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.employees.employee import Employee
    from zoo_simulation.repositories.interfaces.finance_repository import FinanceRepository

_EMPLOYEE_TYPE_TO_CLASS = {
    "Zookeeper": ("zoo_simulation.domain.employees.zookeeper", "Zookeeper"),
    "Veterinarian": ("zoo_simulation.domain.employees.veterinarian", "Veterinarian"),
    "Administrator": ("zoo_simulation.domain.employees.administrator", "Administrator"),
}

# employee_type values whose constructor needs a FinanceManager in addition
# to id/name/salary - see module docstring, "Fixed 2026-08-09".
_TYPES_REQUIRING_FINANCE_MANAGER = frozenset({"Administrator"})


class SQLEmployeeRepository(EmployeeRepository):
    """SQLEmployeeRepository - persists Employee objects in the `employee` table.

        - Constructor: stores the DatabaseConnection used for all queries,
          plus the FinanceRepository needed to reconstruct Administrator
          rows (see module docstring); does not open/close the connection
          itself (owned by the caller, e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `employee` table.
        - _finance_repository (FinanceRepository): used by
          `_row_to_employee()` to build the FinanceManager an
          Administrator requires.
        - Module-level _EMPLOYEE_TYPE_TO_CLASS: maps the `employee_type`
          discriminator column to the (module, class name) used to
          reconstruct the correct concrete Employee subclass when reading
          a row.
    """

    def __init__(
        self, connection: DatabaseConnection, finance_repository: FinanceRepository
    ) -> None:
        """Store the DatabaseConnection and FinanceRepository used for Employee persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).
            finance_repository (FinanceRepository): used by
                `_row_to_employee()` to build a FinanceManager when
                reconstructing an Administrator (see module docstring).

        Test:
            - Given a connected DatabaseConnection and a FinanceRepository,
              when SQLEmployeeRepository is constructed, then
              save()/get_by_id()/get_all()/update()/delete() can be called
              immediately without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection
        self._finance_repository = finance_repository

    def save(self, employee: Employee, zoo_id: int) -> int:
        """Insert a new Employee row.

        Args:
            employee (Employee): the Employee instance to insert (any
                concrete subclass: Zookeeper, Veterinarian, Administrator,
                ...). Its `employee_type` discriminator is derived from
                `type(employee).__name__`, not a separate attribute.
            zoo_id (int): id of the Zoo the employee belongs to.

        Returns:
            int: the employee_id assigned by SQLite (cursor.lastrowid).
            The caller is responsible for making the id available on its
            own Employee reference - this method does not assume
            `employee.id` is settable (Backend domain objects such as
            Transaction expose `id` as a read-only property with no
            setter, so Employee is expected to follow the same pattern).

        Test:
            - Given a new, valid Employee object and an existing zoo_id,
              when save() is called, then the returned id is a positive
              int and get_by_id(that id) afterwards returns matching data.
            - Given a database connection failure (e.g. a locked file),
              when save() is called, then the transaction is rolled back,
              no partial row is written, and no id is returned.
        """
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO employee (zoo_id, employee_type, name, salary)
                VALUES (?, ?, ?, ?)
                """,
                (zoo_id, type(employee).__name__, employee.name, employee.salary),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Load a single Employee row by its primary key.

        Args:
            employee_id (int): primary key of the Employee to load.

        Returns:
            Employee | None: the matching Employee instance (as its
            correct concrete subclass), or None if no row with that ID
            exists.

        Test:
            - Given an employee_id that exists with employee_type
              "Veterinarian", when get_by_id() is called, then the
              returned object is a Veterinarian instance whose attributes
              match the stored row.
            - Given an employee_id that does not exist, when get_by_id()
              is called, then None is returned instead of raising an
              unhandled exception.
        """
        row = self._connection.execute(
            "SELECT * FROM employee WHERE employee_id = ?", (employee_id,)
        ).fetchone()
        return self._row_to_employee(row) if row is not None else None

    def get_all(self) -> list[Employee]:
        """Load every stored Employee row.

        Returns:
            list[Employee]: all Employee instances currently persisted,
            each as its correct concrete subclass.

        Test:
            - Given 3 stored employees of different roles, when get_all()
              is called, then a list of length 3 is returned with each
              entry as its correct concrete subclass.
            - Given no stored employees, when get_all() is called, then an
              empty list is returned, not None.
        """
        rows = self._connection.execute("SELECT * FROM employee").fetchall()
        shared_finance_manager = None
        if any(row["employee_type"] in _TYPES_REQUIRING_FINANCE_MANAGER for row in rows):
            shared_finance_manager = FinanceManager(balance=self._finance_repository.get_balance())
        return [self._row_to_employee(row, finance_manager=shared_finance_manager) for row in rows]

    def update(self, employee: Employee) -> None:
        """Update an existing Employee row.

        Args:
            employee (Employee): the Employee instance with updated
                attribute values (e.g. after a salary change).

        Test:
            - Given an existing Employee whose salary changed, when
              update() is called, then get_by_id() returns the new value
              afterwards.
            - Given an Employee whose id does not exist in storage, when
              update() is called, then zero rows are affected and no
              exception is raised (no silent row creation, NFR-09).
        """
        try:
            self._connection.execute(
                "UPDATE employee SET name = ?, salary = ? WHERE employee_id = ?",
                (employee.name, employee.salary, employee.id),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def delete(self, employee_id: int) -> None:
        """Remove an Employee row from storage.

        Args:
            employee_id (int): primary key of the Employee to delete.

        Test:
            - Given an employee_id that exists, when delete() is called,
              then a subsequent get_by_id() for that id returns None.
            - Given an employee_id that does not exist, when delete() is
              called, then no exception is raised (0 rows affected,
              no-op instead of crash).
        """
        try:
            self._connection.execute(
                "DELETE FROM employee WHERE employee_id = ?", (employee_id,)
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _row_to_employee(self, row: sqlite3.Row, finance_manager: FinanceManager | None = None) -> Employee:
        """Build the correct concrete Employee subclass from one `employee` row.

        Args:
            row (sqlite3.Row): one row from the `employee` table
                (row_factory = sqlite3.Row, see
                SQLiteConnection.connect()).
            finance_manager (FinanceManager | None, optional): a
                pre-built FinanceManager to reuse for this row if it
                turns out to be an Administrator, instead of querying
                `get_balance()` again. `get_all()` builds one shared
                instance up front so N stored Administrators cost one
                `get_balance()` call, not N. Defaults to None, in which
                case a fresh one is built on demand (used by
                `get_by_id()`, where only a single row is ever loaded).

        Returns:
            Employee: a Zookeeper/Veterinarian/Administrator instance
            populated from the row, chosen via the `employee_type`
            discriminator column. Administrator rows additionally get a
            freshly-built `FinanceManager` (see module docstring, "Fixed
            2026-08-09").

        Test:
            - Given a row with employee_type="Zookeeper", when
              _row_to_employee() is called, then a Zookeeper instance is
              returned with attributes equal to the row's values.
            - Given a row with employee_type="Administrator", when
              _row_to_employee() is called, then an Administrator instance
              is returned whose `record_income()`/`record_expense()` can
              be called immediately (its FinanceManager is present and
              usable), instead of raising TypeError.
            - Given a row with an employee_type value not present in
              _EMPLOYEE_TYPE_TO_CLASS (e.g. corrupted data), when
              _row_to_employee() is called, then a ValueError is raised
              instead of silently returning a wrong/generic object.
        """
        employee_type = row["employee_type"]
        if employee_type not in _EMPLOYEE_TYPE_TO_CLASS:
            raise ValueError(f"Unknown employee_type stored in database: {employee_type!r}")

        module_path, class_name = _EMPLOYEE_TYPE_TO_CLASS[employee_type]
        employee_class = getattr(importlib.import_module(module_path), class_name)

        extra_kwargs = {}
        if employee_type in _TYPES_REQUIRING_FINANCE_MANAGER:
            extra_kwargs["finance_manager"] = finance_manager or FinanceManager(
                balance=self._finance_repository.get_balance()
            )

        return employee_class(
            id=row["employee_id"],
            name=row["name"],
            salary=row["salary"],
            **extra_kwargs,
        )
