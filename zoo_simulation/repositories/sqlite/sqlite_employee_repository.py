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

"""

from __future__ import annotations

import importlib
import sqlite3
from typing import TYPE_CHECKING

from zoo_simulation.repositories.interfaces.employee_repository import EmployeeRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.employees.employee import Employee

_EMPLOYEE_TYPE_TO_CLASS = {
    "Zookeeper": ("zoo_simulation.domain.employees.zookeeper", "Zookeeper"),
    "Veterinarian": ("zoo_simulation.domain.employees.veterinarian", "Veterinarian"),
    "Administrator": ("zoo_simulation.domain.employees.administrator", "Administrator"),
}


class SQLEmployeeRepository(EmployeeRepository):
    """SQLEmployeeRepository - persists Employee objects in the `employee` table.

        - Constructor: stores the DatabaseConnection used for all queries;
          does not open/close the connection itself (owned by the caller,
          e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `employee` table.
        - Module-level _EMPLOYEE_TYPE_TO_CLASS: maps the `employee_type`
          discriminator column to the (module, class name) used to
          reconstruct the correct concrete Employee subclass when reading
          a row.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """Store the DatabaseConnection used for all Employee persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).

        Test:
            - Given a connected DatabaseConnection, when
              SQLEmployeeRepository is constructed, then
              save()/get_by_id()/get_all()/update()/delete() can be called
              immediately without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection

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
            `employee.id` is set to this value before returning, so the
            caller's reference is immediately usable for get_by_id()/
            update() without a re-fetch.

        Test:
            - Given a new, valid Employee object and an existing zoo_id,
              when save() is called, then a new row is inserted, the
              returned id (and employee.id) match, and get_by_id()
              afterwards returns matching data.
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
            employee.id = cursor.lastrowid
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
        return [self._row_to_employee(row) for row in rows]

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

    def _row_to_employee(self, row: sqlite3.Row) -> Employee:
        """Build the correct concrete Employee subclass from one `employee` row.

        Args:
            row (sqlite3.Row): one row from the `employee` table
                (row_factory = sqlite3.Row, see
                SQLiteConnection.connect()).

        Returns:
            Employee: a Zookeeper/Veterinarian/Administrator instance
            populated from the row, chosen via the `employee_type`
            discriminator column.

        Test:
            - Given a row with employee_type="Zookeeper", when
              _row_to_employee() is called, then a Zookeeper instance is
              returned with attributes equal to the row's values.
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

        return employee_class(
            id=row["employee_id"],
            name=row["name"],
            salary=row["salary"],
        )
