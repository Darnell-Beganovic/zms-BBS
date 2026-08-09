"""FinanceManager: tracks zoo income, expenses and balance.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from zoo_simulation.domain.transaction import Transaction


class FinanceManager:
    """FinanceManager - tracks the zoo's running balance and creates Transactions.

    Only keeps a running `balance` (matching the class diagram's single
    `-float balance` attribute), not the full list of created
    Transactions - each `record_income()`/`record_expense()` call
    returns the new Transaction so the caller (e.g. ZooService) can pass
    it on to FinanceRepository.save_transaction() for persistence;
    FinanceManager itself never talks to a repository (Dependency
    Inversion stays with the service layer).

        - Constructor: stores `balance` privately; changes only through
          `record_income()`/`record_expense()`, never assigned directly.
        - _balance (float): current balance, positive or negative.
    """

    def __init__(self, balance: float = 0.0) -> None:
        """Create a FinanceManager with a starting balance.

        Args:
            balance (float, optional): starting balance, e.g. loaded via
                FinanceRepository.get_balance() for an existing zoo.
                Defaults to 0.0 for a brand-new zoo.

        Test:
            - Given balance=500.0, when the constructor is called, then
              `.get_balance()` returns 500.0.
            - Given no argument, when the constructor is called, then
              `.get_balance()` returns 0.0.
        """
        self._balance = balance

    def get_balance(self) -> float:
        """Return the current balance.

        Returns:
            float: the current balance.

        Test:
            - Given a freshly constructed FinanceManager with balance=0.0,
              when `get_balance()` is called, then it returns 0.0.
            - Given `record_income(100.0, "Ticket")` was called, when
              `get_balance()` is called afterwards, then it returns 100.0.
        """
        return self._balance

    def record_income(self, amount: float, description: str) -> Transaction:
        """Record an income event and increase the balance.

        Args:
            amount (float): the income amount, as a positive magnitude
                (the sign convention - positive for income - is applied
                internally when the Transaction is created).
            description (str): human-readable note, e.g. "Ticket sale".

        Returns:
            Transaction: the newly created, valid income Transaction.

        Raises:
            ValueError: if `amount` is not strictly positive.

        Test:
            - Given balance=0.0, when `record_income(100.0, "Ticket")` is
              called, then `.get_balance()` becomes 100.0 and the
              returned Transaction has `transaction_type="income"` and
              `amount=100.0`.
            - Given amount=0.0, when `record_income()` is called, then a
              ValueError is raised and the balance stays unchanged.
        """
        if amount <= 0:
            raise ValueError("Income amount must be positive.")
        self._balance += amount
        return Transaction(transaction_type="income", amount=amount, description=description)

    def record_expense(self, amount: float, description: str) -> Transaction:
        """Record an expense event and decrease the balance.

        Args:
            amount (float): the expense amount, as a positive magnitude
                (internally stored as a negative Transaction.amount, per
                Transaction's sign convention).
            description (str): human-readable note, e.g. "Feed cost".

        Returns:
            Transaction: the newly created, valid expense Transaction.

        Raises:
            ValueError: if `amount` is not strictly positive.

        Test:
            - Given balance=500.0, when `record_expense(50.0, "Feed
              cost")` is called, then `.get_balance()` becomes 450.0 and
              the returned Transaction has `transaction_type="expense"`
              and `amount=-50.0`.
            - Given amount=-10.0, when `record_expense()` is called, then
              a ValueError is raised and the balance stays unchanged.
        """
        if amount <= 0:
            raise ValueError("Expense amount must be positive.")
        self._balance -= amount
        return Transaction(transaction_type="expense", amount=-amount, description=description)
