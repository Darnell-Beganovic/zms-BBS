"""sqlite_finance_repository.py - SQLite implementation of FinanceRepository.

    Implements FinanceRepository
    (repositories/interfaces/finance_repository.py) against the
    `transaction` table defined in database/schema.sql, using a
    DatabaseConnection (SQLiteConnection in practice) for all SQL access.
    Assumes Transaction's constructor accepts id/transaction_type/amount/
    description/created_at as keyword arguments, and that `amount` already
    carries its sign (positive for income, negative for expense), so
    get_balance() is a plain SUM(amount). Schwerpunkt: Datenbank - Kaiss
    Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pandas as pd

from zoo_simulation.repositories.interfaces.finance_repository import FinanceRepository

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.transaction import Transaction

_TRANSACTION_COLUMNS = (
    "transaction_id",
    "zoo_id",
    "transaction_type",
    "amount",
    "description",
    "created_at",
)


class SQLFinanceRepository(FinanceRepository):
    """SQLFinanceRepository - persists Transaction objects in the `transaction` table.

        - Constructor: stores the DatabaseConnection used for all queries;
          does not open/close the connection itself (owned by the caller,
          e.g. main.py).
        - _connection (DatabaseConnection): the connection used to run SQL
          statements against the `transaction` table.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """Store the DatabaseConnection used for all Transaction persistence.

        Args:
            connection (DatabaseConnection): an already-connected
                DatabaseConnection (e.g. SQLiteConnection).

        Test:
            - Given a connected DatabaseConnection, when
              SQLFinanceRepository is constructed, then
              save_transaction()/get_all_transactions()/get_balance() can
              be called immediately without any further setup.
            - Given the same connection instance is shared with other
              SQL*Repository objects, when both are used, then they
              operate against the same underlying database file and
              transaction.
        """
        self._connection = connection

    def save_transaction(self, transaction: Transaction, zoo_id: int) -> int:
        """Insert a new Transaction row.

        Args:
            transaction (Transaction): the Transaction instance to insert.
            zoo_id (int): id of the Zoo the transaction belongs to.

        Returns:
            int: the transaction_id assigned by SQLite (cursor.lastrowid).
            The caller is responsible for making the id available on its
            own Transaction reference - this method does not assume
            `transaction.id` is settable (Transaction exposes `id` as a
            read-only property with no setter).

        Test:
            - Given a new, valid Transaction and an existing zoo_id, when
              save_transaction() is called, then the returned id is a
              positive int and it appears in get_all_transactions()
              afterwards with matching data.
            - Given a database connection failure (e.g. a locked file),
              when save_transaction() is called, then the transaction is
              rolled back, no partial row is written, and no id is
              returned.
        """
        created_at = transaction.created_at
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()

        try:
            cursor = self._connection.execute(
                """
                INSERT INTO "transaction"
                    (zoo_id, transaction_type, amount, description, created_at)
                VALUES (?, ?, ?, ?, COALESCE(?, STRFTIME('%Y-%m-%dT%H:%M:%S', 'now')))
                """,
                (zoo_id, transaction.transaction_type, transaction.amount,
                 transaction.description, created_at),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise

    def get_all_transactions(self) -> list[Transaction]:
        """Load every stored Transaction row.

        Returns:
            list[Transaction]: all Transaction instances currently
            persisted.

        Test:
            - Given 4 stored transactions, when get_all_transactions() is
              called, then a list of length 4 is returned.
            - Given no stored transactions, when get_all_transactions() is
              called, then an empty list is returned, not None.
        """
        rows = self._connection.execute('SELECT * FROM "transaction"').fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def get_balance(self) -> float:
        """Compute the current balance from all stored transactions.

        Returns:
            float: sum of all transaction amounts (income positive,
            expense negative).

        Test:
            - Given transactions totalling +500 income and -200 expenses,
              when get_balance() is called, then 300 is returned.
            - Given no transactions exist yet, when get_balance() is
              called, then 0 is returned instead of raising an error.
        """
        row = self._connection.execute(
            'SELECT COALESCE(SUM(amount), 0) AS balance FROM "transaction"'
        ).fetchone()
        return row["balance"]

    def get_as_dataframe(self) -> pd.DataFrame:
        """Load every stored Transaction row as a pandas DataFrame.

        Used by ReportService to build the financial report and export it
        as CSV/Excel.

        Returns:
            pd.DataFrame: one row per Transaction, columns matching the
            `transaction` table.

        Test:
            - Given 4 stored transactions, when get_as_dataframe() is
              called, then a DataFrame with 4 rows and the expected
              column names is returned.
            - Given no stored transactions, when get_as_dataframe() is
              called, then an empty DataFrame with the correct columns
              (not None) is returned, so ReportService can still export a
              valid empty report.
        """
        rows = self._connection.execute('SELECT * FROM "transaction"').fetchall()
        if not rows:
            return pd.DataFrame(columns=_TRANSACTION_COLUMNS)
        return pd.DataFrame([dict(row) for row in rows], columns=list(_TRANSACTION_COLUMNS))

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        """Build a Transaction domain object from one `transaction` table row.

        Args:
            row (sqlite3.Row): one row from the `transaction` table
                (row_factory = sqlite3.Row, see
                SQLiteConnection.connect()).

        Returns:
            Transaction: a Transaction instance populated from the row.

        Test:
            - Given a row with all columns set, when _row_to_transaction()
              is called, then the returned Transaction's attributes equal
              the row's values (row["transaction_id"] -> Transaction.id,
              etc.).
            - Given a row where description is NULL, when
              _row_to_transaction() is called, then
              Transaction.description is None instead of raising a
              conversion error.
        """
        from zoo_simulation.domain.transaction import Transaction

        return Transaction(
            id=row["transaction_id"],
            transaction_type=row["transaction_type"],
            amount=row["amount"],
            description=row["description"],
            created_at=row["created_at"],
        )
