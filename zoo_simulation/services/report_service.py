"""report_service.py - builds animal/financial/inventory reports and exports them as CSV/Excel.

    Thin layer over the three repositories' get_as_dataframe() methods
    (AnimalRepository, FinanceRepository, InventoryRepository): each
    create_*_report() call simply delegates to the matching repository, so
    ReportService never runs SQL itself and never depends on
    SQLAnimalRepository/SQLFinanceRepository/SQLInventoryRepository
    directly - only on the interfaces (Dependency Inversion Principle).
    export_csv()/export_excel() wrap pandas' DataFrame.to_csv()/to_excel()
    (openpyxl is the .xlsx engine pandas picks automatically, see
    requirements.txt). Lives in services/ for architectural reasons
    (Service Layer), but is owned by the Database focus since it is
    purely a thin layer over repository data. Schwerpunkt: Datenbank
    (Service Layer / Reporting) - Kaiss Saleh.

    author: Kaiss Saleh
    date: 2026-08-05
    version: 1.0.0
    license: Educational Use - Programming II Module

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from zoo_simulation.repositories.interfaces.animal_repository import AnimalRepository
    from zoo_simulation.repositories.interfaces.finance_repository import FinanceRepository
    from zoo_simulation.repositories.interfaces.inventory_repository import InventoryRepository


class ReportService:
    """ReportService - builds and exports animal/financial/inventory reports.

        - Constructor: stores the three repository interfaces used to
          build reports; never talks to the database directly.
        - _animal_repository (AnimalRepository): source for the animal
          report.
        - _finance_repository (FinanceRepository): source for the
          financial report.
        - _inventory_repository (InventoryRepository): source for the
          inventory report.
    """

    def __init__(
        self,
        animal_repository: AnimalRepository,
        finance_repository: FinanceRepository,
        inventory_repository: InventoryRepository,
    ) -> None:
        """Store the repositories used to build every report.

        Args:
            animal_repository (AnimalRepository): repository providing
                animal data via get_as_dataframe().
            finance_repository (FinanceRepository): repository providing
                transaction data via get_as_dataframe().
            inventory_repository (InventoryRepository): repository
                providing food/medication data via get_as_dataframe().

        Test:
            - Given three connected repositories, when ReportService is
              constructed, then create_animal_report()/
              create_financial_report()/create_inventory_report() can be
              called immediately without any further setup.
            - Given repository doubles (e.g. fakes in a test), when
              ReportService is constructed with them instead of the real
              SQL*Repository classes, then it works identically, since it
              only depends on the repository interfaces.
        """
        self._animal_repository = animal_repository
        self._finance_repository = finance_repository
        self._inventory_repository = inventory_repository

    def create_animal_report(self) -> pd.DataFrame:
        """Build the animal report.

        Returns:
            pd.DataFrame: one row per Animal, as returned by
            AnimalRepository.get_as_dataframe().

        Test:
            - Given 3 stored animals, when create_animal_report() is
              called, then a DataFrame with 3 rows is returned.
            - Given no stored animals, when create_animal_report() is
              called, then an empty DataFrame is returned instead of None,
              so export_csv()/export_excel() can still run on it.
        """
        return self._animal_repository.get_as_dataframe()

    def create_financial_report(self) -> pd.DataFrame:
        """Build the financial report.

        Returns:
            pd.DataFrame: one row per Transaction, as returned by
            FinanceRepository.get_as_dataframe().

        Test:
            - Given 4 stored transactions, when create_financial_report()
              is called, then a DataFrame with 4 rows is returned.
            - Given no stored transactions, when create_financial_report()
              is called, then an empty DataFrame is returned instead of
              None.
        """
        return self._finance_repository.get_as_dataframe()

    def create_inventory_report(self) -> pd.DataFrame:
        """Build the inventory report.

        Returns:
            pd.DataFrame: one row per FoodItem/Medication, as returned by
            InventoryRepository.get_as_dataframe().

        Test:
            - Given 3 food items and 2 medications in stock, when
              create_inventory_report() is called, then a DataFrame with 5
              rows is returned.
            - Given an empty inventory, when create_inventory_report() is
              called, then an empty DataFrame is returned instead of None.
        """
        return self._inventory_repository.get_as_dataframe()

    def export_csv(self, data: pd.DataFrame, file_path: str) -> None:
        """Write a report DataFrame to a CSV file.

        Args:
            data (pd.DataFrame): the report to export, e.g. the result of
                create_animal_report().
            file_path (str): destination path for the CSV file.

        Test:
            - Given a non-empty report DataFrame and a writable file_path,
              when export_csv() is called, then a CSV file is created at
              file_path with a header row and one row per DataFrame row.
            - Given file_path points to a directory that does not exist,
              when export_csv() is called, then the underlying OSError is
              raised instead of silently failing.
        """
        data.to_csv(file_path, index=False)

    def export_excel(self, data: pd.DataFrame, file_path: str) -> None:
        """Write a report DataFrame to an Excel (.xlsx) file.

        Args:
            data (pd.DataFrame): the report to export, e.g. the result of
                create_financial_report().
            file_path (str): destination path for the Excel file.

        Test:
            - Given a non-empty report DataFrame and a writable file_path
              ending in .xlsx, when export_excel() is called, then an
              Excel file is created at file_path readable by pandas'
              read_excel() with the same data.
            - Given an empty report DataFrame, when export_excel() is
              called, then an Excel file with only the header row is
              created instead of raising an error.
        """
        data.to_excel(file_path, index=False)
