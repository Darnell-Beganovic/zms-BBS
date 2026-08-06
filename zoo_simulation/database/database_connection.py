"""database_connection.py - database connection abstraction (Persistence Layer)

    Defines the DatabaseConnection interface that all repositories depend on
    (Dependency Inversion Principle, NFR-08) and SQLiteConnection, the only
    concrete implementation planned for this project (NFR-05, see
    Projektplanung/Funktionale_und_nichtfunktionale_Anforderungen.md).
    Schwerpunkt: Datenbank - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

from abc import ABC, abstractmethod
import sqlite3


class DatabaseConnection(ABC):
    """DatabaseConnection - abstract interface for a database connection.

        - No constructor: this is a pure interface (ABC) and is never
          instantiated directly.
        - No stored state: concrete subclasses own their own connection
          state (e.g. file path, open connection handle).
        - Repositories depend only on this interface, never on a concrete
          implementation, so the persistence backend can be replaced with
          minimal changes (Open/Closed Principle, NFR-08).
    """

    @abstractmethod
    def connect(self) -> None:
        """Open the database connection.

        Test:
            - Any implementation, when connect() succeeds, must leave the
              object ready to accept execute()/commit()/rollback() calls.
            - Any implementation, when the underlying resource is
              unavailable (e.g. invalid path/permissions), must raise an
              exception instead of silently continuing.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, query: str, parameters: tuple = ()) -> object:
        """Execute a single SQL statement.

        Args:
            query (str): SQL statement, optionally with '?' placeholders.
            parameters (tuple, optional): values bound to the placeholders
                in `query`. Defaults to an empty tuple.

        Returns:
            object: a cursor-like object that callers can use to read
            query results (e.g. fetchone()/fetchall()) or the ID of an
            inserted row.

        Test:
            - Any implementation must accept a query string and a
              parameters tuple and return an object usable to read query
              results.
            - Any implementation must safely handle an empty parameters
              tuple for queries without placeholders.
        """
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction.

        Test:
            - Any implementation must make all statements executed since
              the last commit/rollback durable.
            - Any implementation must be safe to call when there is
              nothing pending to commit.
        """
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """Roll back the current transaction.

        Test:
            - Any implementation must discard all statements executed
              since the last commit.
            - Any implementation must be safe to call when there is
              nothing pending to roll back.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the database connection.

        Test:
            - Any implementation must release the underlying resource so
              the process can exit cleanly / the file is not left locked.
            - Any implementation must be safe to call multiple times
              (idempotent close).
        """
        raise NotImplementedError


class SQLiteConnection(DatabaseConnection):
    """SQLiteConnection - SQLite implementation of DatabaseConnection.

        - Constructor: stores the target database file path; does not open
          a connection yet (lazy connect via connect()).
        - _database_path (str): filesystem path to the SQLite database
          file.
        - _connection (sqlite3.Connection | None): the underlying sqlite3
          connection once connect() has been called, otherwise None.

        Wraps the standard library sqlite3 module. Foreign key enforcement
        is enabled on every new connection so that invalid operations
        cannot corrupt referential integrity between tables (NFR-09).
    """

    def __init__(self, database_path: str) -> None:
        """Store the database file path without opening a connection yet.

        Args:
            database_path (str): filesystem path to the SQLite database
                file (e.g. "database/zoo.db").

        Test:
            - Given a database_path string, when SQLiteConnection is
              constructed, then no file I/O happens yet and _connection is
              None until connect() is called (lazy connection).
            - Given the same instance, when connect() then close() are
              called, then the instance can be reconnected via connect()
              again (the object stays reusable).
        """
        self._database_path = database_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open the SQLite connection and enable foreign key enforcement.

        Test:
            - Given a valid file path, when connect() is called, then a
              usable sqlite3 connection is opened and
              "PRAGMA foreign_keys" reports ON.
            - Given a path whose parent directory does not exist, when
              connect() is called, then sqlite3 raises an
              sqlite3.OperationalError.
        """
        self._connection = sqlite3.connect(self._database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def execute(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement against the open connection.

        Args:
            query (str): SQL statement, optionally with '?' placeholders.
            parameters (tuple, optional): values bound to the placeholders
                in `query`. Defaults to an empty tuple.

        Returns:
            sqlite3.Cursor: cursor positioned on the statement's result,
            usable for fetchone()/fetchall() or reading lastrowid.

        Test:
            - Given a valid SELECT query and an open connection, when
              execute() is called, then the returned cursor's fetchall()
              returns the expected rows.
            - Given execute() is called before connect(), then a
              RuntimeError is raised instead of an unhandled
              AttributeError.
        """
        return self._require_connection().execute(query, parameters)

    def commit(self) -> None:
        """Commit the current transaction on the open connection.

        Test:
            - Given pending changes after an INSERT, when commit() is
              called, then the changes are persisted and visible from a
              new connection to the same file.
            - Given commit() is called before connect(), then a
              RuntimeError is raised.
        """
        self._require_connection().commit()

    def rollback(self) -> None:
        """Roll back the current transaction on the open connection.

        Test:
            - Given pending changes after an INSERT without a commit,
              when rollback() is called, then the changes are discarded
              and not visible afterwards.
            - Given rollback() is called before connect(), then a
              RuntimeError is raised.
        """
        self._require_connection().rollback()

    def close(self) -> None:
        """Close the SQLite connection if one is open.

        Test:
            - Given an open connection, when close() is called, then a
              subsequent execute() call raises a RuntimeError (connection
              cleared).
            - Given close() is called twice in a row (already closed),
              then no exception is raised (idempotent).
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _require_connection(self) -> sqlite3.Connection:
        """Return the open connection or raise if connect() was not called.

        Returns:
            sqlite3.Connection: the currently open connection.

        Test:
            - Given self._connection is None, when _require_connection()
              is called, then a RuntimeError with a clear message is
              raised.
            - Given self._connection is set (connect() was called), when
              _require_connection() is called, then it returns that same
              connection object.
        """
        if self._connection is None:
            raise RuntimeError(
                "SQLiteConnection.connect() must be called before using the connection."
            )
        return self._connection
