"""Administrator employee: manages zoo finances.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.employees.employee import Employee

if TYPE_CHECKING:
    from zoo_simulation.domain.finance_manager import FinanceManager


class Administrator(Employee):
    """Administrator - manages the zoo's finances via a FinanceManager.

    `Administrator ..> FinanceManager : manages` (class diagram) is a
    dependency, not a diagram attribute, but `record_income(amount)`/
    `record_expense(amount)` need a FinanceManager to actually delegate
    to - so the constructor takes one and stores it privately (a Backend
    implementation addition, documented in
    planning_backend_darnell.md - same pattern as Animal's
    `adjust_health()`/`adjust_hunger()`/`adjust_energy()` additions).

        - _finance_manager (FinanceManager): used by
          `record_income()`/`record_expense()`; not persisted as part of
          Administrator itself (Zoo owns the one FinanceManager, see the
          class diagram's `Zoo *-- "1" FinanceManager` composition).
    """

    def __init__(
        self,
        name: str,
        finance_manager: FinanceManager,
        salary: float = 0.0,
        id: int | None = None,
    ) -> None:
        """Create an Administrator.

        Args:
            name (str): e.g. "Jamie Fox".
            finance_manager (FinanceManager): the zoo's FinanceManager,
                used by `record_income()`/`record_expense()`.
            salary (float, optional): monthly salary. Defaults to 0.0.
            id (int | None, optional): primary key if loaded from
                storage. Defaults to None.

        Test:
            - Given a FinanceManager instance, when the constructor is
              called, then `record_income()`/`record_expense()` can be
              called immediately without further setup.
            - Given name="Jamie Fox", when the constructor is called,
              then `.name` is "Jamie Fox".
        """
        super().__init__(name=name, salary=salary, id=id)
        self._finance_manager = finance_manager

    def perform_task(self) -> str:
        """Describe this employee's daily routine. Pure, no side effects.

        Returns:
            str: a human-readable description.

        Test:
            - When `perform_task()` is called, then it returns a
              non-empty string mentioning managing finances.
            - When called twice, then it returns the same string both
              times (pure, no state change) - actual bookkeeping happens
              via `record_income()`/`record_expense()` instead.
        """
        return "Manages the zoo's income, expenses and overall budget."

    def record_income(self, amount: float) -> None:
        """Record an income event via the zoo's FinanceManager.

        Args:
            amount (float): the income amount (positive magnitude).

        Test:
            - Given balance=0.0, when `record_income(100.0)` is called,
              then the FinanceManager's balance becomes 100.0.
            - Given amount=0.0, when `record_income()` is called, then a
              ValueError is raised (delegates to
              `FinanceManager.record_income()`'s validation).
        """
        self._finance_manager.record_income(amount, f"Administrator income recorded by {self.name}")

    def record_expense(self, amount: float) -> None:
        """Record an expense event via the zoo's FinanceManager.

        Args:
            amount (float): the expense amount (positive magnitude).

        Test:
            - Given balance=500.0, when `record_expense(50.0)` is
              called, then the FinanceManager's balance becomes 450.0.
            - Given amount=-10.0, when `record_expense()` is called,
              then a ValueError is raised (delegates to
              `FinanceManager.record_expense()`'s validation).
        """
        self._finance_manager.record_expense(amount, f"Administrator expense recorded by {self.name}")
