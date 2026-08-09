"""Administrator employee: manages zoo finances.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.employees.employee import Employee

if TYPE_CHECKING:
    from zoo_simulation.domain.finance_manager import FinanceManager
    from zoo_simulation.domain.transaction import Transaction


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

    def set_finance_manager(self, finance_manager: FinanceManager) -> None:
        """Replace the FinanceManager this Administrator books through.

        Added 2026-08-09 (see planning_backend_darnell.md section 2.11
        and planning_db_kaiss.md section 6, "FinanceManager has no
        persisted identity"): `SQLEmployeeRepository` reconstructs a
        loaded Administrator with its own fresh `FinanceManager`
        (equal in starting balance, but not the same object as `Zoo.
        finance_manager` - a documented, previously harmless quirk
        since nothing ever routed real transactions through
        `Administrator` before `ZooService.sell_ticket()`/
        `feed_animal()` started doing so). `ZooService.get_zoo()` calls
        this once per load to point every employed Administrator at the
        same `Zoo.finance_manager` instance, so `record_income()`/
        `record_expense()` calls are visible via
        `Zoo.finance_manager.get_balance()`, matching this class's own
        docstring ("Zoo owns the one FinanceManager").

        Args:
            finance_manager (FinanceManager): the Zoo's canonical
                FinanceManager to book through from now on.

        Test:
            - Given an Administrator constructed with a throwaway
              FinanceManager, when `set_finance_manager(zoo.
              finance_manager)` is called and then `record_income(50.0,
              "Test")`, then `zoo.finance_manager.get_balance()`
              reflects the change.
            - Given `set_finance_manager()` was called, when
              `record_expense()` is called afterward, then the
              previously-set FinanceManager is used, not the one passed
              to the constructor.
        """
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

    def record_income(self, amount: float, description: str | None = None) -> Transaction:
        """Record an income event via the zoo's FinanceManager.

        Args:
            amount (float): the income amount (positive magnitude).
            description (str | None, optional): human-readable note,
                e.g. "Ticket sale". Defaults to None, which falls back
                to a generic "Administrator income recorded by
                {name}" note. Added 2026-08-09 (see
                `planning_backend_darnell.md` section 2.11) - callers
                such as `ZooService.sell_ticket()` need the specific
                description ("Ticket sale") to show up in the financial
                report, not a generic one.

        Returns:
            Transaction: the newly created Transaction (added
                2026-08-09, was previously void) - `FinanceManager.
                record_income()` already returns it, so `Administrator`
                simply passes it on rather than discarding it, letting
                callers persist it via `FinanceRepository.
                save_transaction()` the same way they would if they
                called `FinanceManager` directly.

        Test:
            - Given balance=0.0, when `record_income(100.0, "Ticket
              sale")` is called, then the FinanceManager's balance
              becomes 100.0 and the returned Transaction's description
              is "Ticket sale".
            - Given amount=0.0, when `record_income()` is called, then a
              ValueError is raised (delegates to
              `FinanceManager.record_income()`'s validation).
        """
        note = description if description is not None else f"Administrator income recorded by {self.name}"
        return self._finance_manager.record_income(amount, note)

    def record_expense(self, amount: float, description: str | None = None) -> Transaction:
        """Record an expense event via the zoo's FinanceManager.

        Args:
            amount (float): the expense amount (positive magnitude).
            description (str | None, optional): human-readable note,
                e.g. "Feeding cost: Simba (Fleisch)". Defaults to None,
                which falls back to a generic "Administrator expense
                recorded by {name}" note. Added 2026-08-09, same
                rationale as `record_income()`'s new parameter.

        Returns:
            Transaction: the newly created Transaction (added
                2026-08-09, was previously void - same rationale as
                `record_income()`).

        Test:
            - Given balance=500.0, when `record_expense(50.0, "Feeding
              cost")` is called, then the FinanceManager's balance
              becomes 450.0 and the returned Transaction's description
              is "Feeding cost".
            - Given amount=-10.0, when `record_expense()` is called,
              then a ValueError is raised (delegates to
              `FinanceManager.record_expense()`'s validation).
        """
        note = description if description is not None else f"Administrator expense recorded by {self.name}"
        return self._finance_manager.record_expense(amount, note)
