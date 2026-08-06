"""Transaction: a single financial income/expense record.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from datetime import datetime


class Transaction:
    """Transaction - an immutable record of one income or expense event.

        - Constructor: stores all attributes privately; there are no
          setters, since a Transaction is not meant to change after it is
          created (FinanceManager creates a new one per income/expense,
          it never edits an existing one).
        - _id (int | None): primary key once persisted, None for a
          transaction that has not been saved yet (see
          FinanceRepository.save_transaction()).
        - _transaction_type (str): "income" or "expense".
        - _amount (float): positive for income, negative for expense
          (sign convention, see is_valid()).
        - _description (str): human-readable note, e.g. "Ticket sale".
        - _created_at (datetime | None): timestamp of creation.
    """

    def __init__(self, transaction_type: str, amount: float = 0.0, description: str = "", id: int | None = None, created_at: datetime | None = None,) -> None:
        """Create a Transaction with the given attributes.

        Args:
            transaction_type (str): "income" or "expense".
            amount (float, optional): positive for income, negative for
                expense. Defaults to 0.0, which is intentionally always
                invalid (see is_valid()) - a caller must consciously
                supply a real amount.
            description (str, optional): human-readable note. Defaults to
                "".
            id (int | None, optional): primary key if this Transaction was
                loaded from storage. Defaults to None for a new,
                not-yet-persisted Transaction.
            created_at (datetime | None, optional): creation timestamp.
                Defaults to None; FinanceRepository.save_transaction() is
                expected to fill this in via the database's default
                (see schema.sql), not this constructor.

        Test:
            - Given transaction_type="income" and amount=100.0, when the
              constructor is called, then the resulting object's
              `.transaction_type` is "income" and `.amount` is 100.0.
            - Given no `id` is passed, when the constructor is called,
              then `.id` is None (new, not-yet-persisted transaction).
        """
        self._id = id
        self._transaction_type = transaction_type
        self._amount = amount
        self._description = description
        self._created_at = created_at

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def transaction_type(self) -> str:
        return self._transaction_type

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def description(self) -> str:
        return self._description

    @property
    def created_at(self) -> datetime | None:
        return self._created_at

    def is_valid(self) -> bool:
        """Check whether this transaction is internally consistent.

        A transaction is valid if `transaction_type` is one of the known
        values and `amount`'s sign matches that type: positive for
        "income", negative for "expense" (see e.g. controller_stub.py's
        seed data for this sign convention). This method is a pure check -
        it never modifies the transaction's own state.

        Returns:
            bool: True if the transaction is consistent, False otherwise.

        Test:
            - Given transaction_type="income" and amount=250.0, when
              is_valid() is called, then it returns True.
            - Given transaction_type="income" and amount=-50.0 (sign
              contradicts the type), when is_valid() is called, then it
              returns False.
            - Given transaction_type="unknown" and any amount, when
              is_valid() is called, then it returns False.
        """
        if not isinstance(self._amount, (int, float)) or isinstance(self._amount, bool):
            return False
        if self._transaction_type == "income":
            return self._amount > 0
        if self._transaction_type == "expense":
            return self._amount < 0
        return False
