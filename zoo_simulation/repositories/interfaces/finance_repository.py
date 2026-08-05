"""finance_repository.py - repository interface for persisting Transaction objects.

    Defines the contract the Backend focus (Darnell) programs against to
    persist/read Transaction objects and compute the current balance,
    without depending on a concrete database technology (Dependency
    Inversion Principle). get_as_dataframe() additionally feeds
    ReportService's financial report / CSV / Excel export. The only
    implementation planned is SQLFinanceRepository
    (repositories/sqlite/sqlite_finance_repository.py). Schwerpunkt:
    Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from zoo_simulation.domain.transaction import Transaction


class FinanceRepository(ABC):
    """FinanceRepository - abstract interface for Transaction persistence.

        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete implementations own their own
          DatabaseConnection.
    """

    @abstractmethod
    def save_transaction(self, transaction: Transaction) -> None:
        """Persist a new Transaction.

        Args:
            transaction (Transaction): the Transaction instance to insert
                (e.g. a ticket sale income or a feed cost expense).

        Test:
            - Any implementation, given a new, valid Transaction, when
              save_transaction() is called, must make it appear in
              get_all_transactions() afterwards with matching data.
            - Any implementation, given a Transaction with a negative
              amount representing an expense, when save_transaction() is
              called, must store it without altering its sign (income vs.
              expense must stay distinguishable, e.g. via
              transaction_type).
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_transactions(self) -> list[Transaction]:
        """Retrieve every stored Transaction.

        Returns:
            list[Transaction]: all Transaction instances currently
            persisted.

        Test:
            - Any implementation, given 4 stored transactions, when
              get_all_transactions() is called, must return a list of
              length 4.
            - Any implementation, given no stored transactions, when
              get_all_transactions() is called, must return an empty
              list, not None.
        """
        raise NotImplementedError

    @abstractmethod
    def get_balance(self) -> float:
        """Compute the current balance from all stored transactions.

        Returns:
            float: sum of all income transactions minus all expense
            transactions.

        Test:
            - Any implementation, given transactions totalling +500
              income and -200 expenses, when get_balance() is called,
              must return 300.
            - Any implementation, given no transactions exist yet, when
              get_balance() is called, must return 0 instead of raising
              an error.
        """
        raise NotImplementedError

    @abstractmethod
    def get_as_dataframe(self) -> pd.DataFrame:
        """Retrieve every stored Transaction as a pandas DataFrame.

        Used by ReportService to build the financial report and export it
        as CSV/Excel.

        Returns:
            pd.DataFrame: one row per Transaction, one column per
            attribute.

        Test:
            - Any implementation, given 4 stored transactions, when
              get_as_dataframe() is called, must return a DataFrame with
              4 rows and the expected column names.
            - Any implementation, given no stored transactions, when
              get_as_dataframe() is called, must return an empty
              DataFrame with the correct columns (not None), so
              ReportService can still export a valid empty report.
        """
        raise NotImplementedError
