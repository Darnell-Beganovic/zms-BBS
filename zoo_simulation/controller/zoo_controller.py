"""ZooController: mediates between the Flask frontend (Alessio) and the service layer.

Schwerpunkt: Backend (Controller Layer) - Darnell Beganovic
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from zoo_simulation.domain.animals.giraffe import Giraffe
from zoo_simulation.domain.animals.lion import Lion
from zoo_simulation.domain.animals.penguin import Penguin
from zoo_simulation.domain.behaviors.feeding_behavior import FeedingBehavior
from zoo_simulation.domain.behaviors.rest_behavior import RestBehavior
from zoo_simulation.domain.behaviors.social_behavior import SocialBehavior
from zoo_simulation.domain.employees.administrator import Administrator
from zoo_simulation.domain.employees.veterinarian import Veterinarian
from zoo_simulation.domain.employees.zookeeper import Zookeeper
from zoo_simulation.domain.food_item import FoodItem
from zoo_simulation.domain.medication import Medication

if TYPE_CHECKING:
    from zoo_simulation.database.database_connection import DatabaseConnection
    from zoo_simulation.domain.behaviors.behavior import Behavior
    from zoo_simulation.repositories.interfaces.employee_repository import EmployeeRepository
    from zoo_simulation.repositories.interfaces.enclosure_repository import EnclosureRepository
    from zoo_simulation.repositories.interfaces.inventory_repository import InventoryRepository
    from zoo_simulation.services.simulation_service import SimulationService
    from zoo_simulation.services.zoo_service import ZooService

    # ReportService is owned by the Database focus (Kaiss); only its
    # already-merged public interface is used here (Dependency
    # Inversion still applies conceptually, even without a formal
    # ReportService ABC).
    from zoo_simulation.services.report_service import ReportService

# Mirrors SQLAnimalRepository's _default_behaviors() defaults (see
# sqlite_animal_repository.py) - a freshly added animal gets the same
# reasonable default Behavior set as a reconstructed one, since Behavior
# objects are never supplied by the frontend's request data.
_DEFAULT_REST_DURATION = 20
_DEFAULT_SOCIAL_LEVEL = 50

_SPECIES_TO_CLASS = {"Lion": Lion, "Giraffe": Giraffe, "Penguin": Penguin}
_DEFAULT_FOOD_PREFERENCE = {"Lion": "meat", "Giraffe": "leaves", "Penguin": "fish"}

_ROLE_TO_CLASS = {"Zookeeper": Zookeeper, "Veterinarian": Veterinarian, "Administrator": Administrator}

_CSV_MIMETYPE = "text/csv"
_XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Enclosure.cleanliness is 0-100 in the domain model (same scale as
# health/hunger/energy), but the frontend's established contract (see
# controller_stub.py's _enclosures and templates/animals_game.html's own
# comment: "enclosure.cleanliness ist im Stub eine Bruchzahl 0-1")
# expects a 0-1 fraction. Converted here, at the presentation boundary,
# rather than changing Enclosure's own internal scale.
_CLEANLINESS_FRACTION_DIVISOR = 100.0

# Default self-wiring for a zero-argument ZooController() (see __init__
# and _build_default_dependencies() below) - used when no explicit
# zoo/simulation/report service is supplied, e.g. by
# zoo_view.py's `_controller = ZooController()`.
_DEFAULT_DATABASE_PATH = str(Path(__file__).resolve().parents[1] / "database" / "zoo.db")
_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

_DEFAULT_ZOO_NAME = "Musterzoo"
_DEFAULT_ZOO_LOCATION = "Berlin"
_DEFAULT_MAXIMUM_VISITORS = 50

# enclosure_type values must match static/js/game.js's SPECIES_HABITATS
# exactly ("Savanna"/"Grassland" for Lion/Giraffe, "Polar"/"Aquatic" for
# Penguin) - that mapping disables every dropdown option whose
# enclosure_type doesn't match the selected species (client-side only,
# see that file's own comment), so a mismatched string here silently
# makes the "adopt animal" form unusable for every species, not just
# Penguin. One enclosure per known habitat, mirroring
# controller_stub.py's own seed data (same names/types), so all three
# species are adoptable out of the box.
_SEED_ENCLOSURES = (
    {"name": "Savannah", "enclosure_type": "Savanna", "size": 200.0, "capacity": 4},
    {"name": "Grassland", "enclosure_type": "Grassland", "size": 150.0, "capacity": 3},
    {"name": "Polar Bay", "enclosure_type": "Polar", "size": 180.0, "capacity": 6},
)
_SEED_FOOD_ITEMS = (
    {"name": "Heu", "food_type": "hay", "quantity": 100.0, "price_per_unit": 3.0, "minimum_quantity": 10.0},
    {"name": "Fleisch", "food_type": "meat", "quantity": 100.0, "price_per_unit": 8.0, "minimum_quantity": 10.0},
    {"name": "Fisch", "food_type": "fish", "quantity": 100.0, "price_per_unit": 5.0, "minimum_quantity": 10.0},
)
# Added 2026-08-09 alongside treat_animal() (see planning_backend_darnell.md
# section 2.10) - without any seeded Medication, the "Behandeln" feature
# would have nothing to treat with.
_SEED_MEDICATIONS = (
    {"name": "Antibiotikum", "quantity": 20.0, "minimum_quantity": 5.0},
    {"name": "Schmerzmittel", "quantity": 20.0, "minimum_quantity": 5.0},
)

# One employee per role, so there is someone to see/interact with from
# the start (added 2026-08-09 alongside hire_employee()/
# clean_enclosure() - see planning_backend_darnell.md section 2.9).
_SEED_EMPLOYEES = (
    {"role": "Zookeeper", "name": "Alex Meier", "salary": 2200.0},
    {"role": "Veterinarian", "name": "Sam Voss", "salary": 2600.0},
    {"role": "Administrator", "name": "Jamie Fox", "salary": 2800.0},
)


def _default_behaviors(food_preference: str) -> list[Behavior]:
    """Build the default Behavior set for a newly added animal.

    Args:
        food_preference (str): fed into the new FeedingBehavior.

    Returns:
        list[Behavior]: `[FeedingBehavior(food_preference),
        SocialBehavior(50), RestBehavior(20)]` - always non-empty,
        satisfying Animal's 1..* Behavior composition requirement.

    Test:
        - Given food_preference="meat", when `_default_behaviors("meat")`
          is called, then the returned list has length 3 and its
          FeedingBehavior's `.food_preference` is "meat".
        - When called twice, then two independent Behavior instances are
          returned each time (not the same shared objects), so mutating
          one animal's behaviors never affects another's.
    """
    return [
        FeedingBehavior(food_preference),
        SocialBehavior(_DEFAULT_SOCIAL_LEVEL),
        RestBehavior(_DEFAULT_REST_DURATION),
    ]


def _apply_schema(connection: DatabaseConnection) -> None:
    """Apply `database/schema.sql` against an open connection.

    Every statement is `CREATE TABLE IF NOT EXISTS`/`CREATE INDEX IF NOT
    EXISTS`, so running this against an already-initialized database is
    a safe no-op. Split naively on `;` rather than using
    `sqlite3.Connection.executescript()` directly, since
    `DatabaseConnection` only exposes single-statement `execute()` (see
    `database_connection.py`) - schema.sql is fully controlled, known
    content with no semicolons inside string literals, so this is safe
    for this specific file.

    Args:
        connection (DatabaseConnection): an already-connected
            DatabaseConnection to apply the schema against.

    Test:
        - Given a brand-new, empty SQLite file, when `_apply_schema()`
          is called, then querying `sqlite_master` afterward lists the
          `zoo`/`enclosure`/`animal`/... tables from schema.sql.
        - Given a database schema.sql was already applied to, when
          `_apply_schema()` is called again, then no error is raised
          (idempotent).
    """
    statements = _SCHEMA_PATH.read_text(encoding="utf-8").split(";")
    for statement in statements:
        statement = statement.strip()
        if statement:
            connection.execute(statement)
    connection.commit()


def _seed_initial_zoo(
    connection: DatabaseConnection,
    enclosure_repository: EnclosureRepository,
    inventory_repository: InventoryRepository,
    employee_repository: EmployeeRepository,
) -> int:
    """Create a first zoo (enclosures, a stocked inventory, starter staff) on an empty database.

    Uses a direct `connection.execute()` for the `zoo` row itself rather
    than `ZooRepository.save(zoo)`: constructing a `Zoo` domain object
    requires already having at least one `Enclosure`/an `Inventory`/a
    `FinanceManager` (`Zoo`'s own `1..*` composition rule), which do not
    exist yet at this exact bootstrap moment - a chicken-and-egg problem
    specific to this one-time seeding step, not a general repository
    capability gap (unlike `InventoryRepository.create_inventory()`,
    which was a real, general gap - see that module's docstring).

    Args:
        connection (DatabaseConnection): used for the one-off `zoo` row
            insert.
        enclosure_repository (EnclosureRepository): used to save the
            seeded Enclosures (see `_SEED_ENCLOSURES`).
        inventory_repository (InventoryRepository): used to create the
            Inventory row and stock it with starter FoodItems.
        employee_repository (EmployeeRepository): used to save the
            seeded Employees (see `_SEED_EMPLOYEES`). The seeded
            Administrator's `FinanceManager` is a throwaway instance
            (`EmployeeRepository.save()` only persists `name`/`salary`/
            `employee_type` - see that interface's docstring) - it plays
            no functional role after this call.

    Returns:
        int: the new zoo's id.

    Test:
        - Given an empty database, when `_seed_initial_zoo()` is called,
          then it returns a positive int and that zoo has exactly 3
          Enclosures, 3 FoodItems and 3 Employees (one per role)
          afterward.
        - Given `_seed_initial_zoo()` was already called once, when
          called again, then a second, independent zoo is created (no
          duplicate-detection here - that is `_build_default_dependencies()`'s
          job, which only calls this when no zoo exists yet).
    """
    from zoo_simulation.domain.enclosure import Enclosure
    from zoo_simulation.domain.finance_manager import FinanceManager

    cursor = connection.execute(
        "INSERT INTO zoo (name, location, current_visitors, maximum_visitors) VALUES (?, ?, ?, ?)",
        (_DEFAULT_ZOO_NAME, _DEFAULT_ZOO_LOCATION, 0, _DEFAULT_MAXIMUM_VISITORS),
    )
    connection.commit()
    zoo_id = cursor.lastrowid

    for enclosure_kwargs in _SEED_ENCLOSURES:
        enclosure_repository.save(Enclosure(**enclosure_kwargs), zoo_id)

    inventory_id = inventory_repository.create_inventory(zoo_id)
    for item_kwargs in _SEED_FOOD_ITEMS:
        inventory_repository.save_item(FoodItem(**item_kwargs), inventory_id)
    for medication_kwargs in _SEED_MEDICATIONS:
        inventory_repository.save_medication(Medication(**medication_kwargs), inventory_id)

    for employee_kwargs in _SEED_EMPLOYEES:
        role = employee_kwargs["role"]
        employee_class = _ROLE_TO_CLASS[role]
        if employee_class is Administrator:
            employee = Administrator(employee_kwargs["name"], FinanceManager(), salary=employee_kwargs["salary"])
        else:
            employee = employee_class(employee_kwargs["name"], salary=employee_kwargs["salary"])
        employee_repository.save(employee, zoo_id)

    return zoo_id


def _build_default_dependencies(
    database_path: str | None = None,
) -> tuple[ZooService, SimulationService, ReportService]:
    """Self-wire a full ZooService/SimulationService/ReportService against a real SQLite database.

    This is the composition root for a zero-argument `ZooController()`
    (see class docstring for why that has to be possible at all).
    Connects to `database_path` (creating/initializing it via
    `_apply_schema()` if needed), builds every `SQL*Repository` with its
    required dependencies, seeds a first zoo via `_seed_initial_zoo()` if
    none exists yet, and wires `ZooService`/`SimulationEngine`/
    `SimulationService`/`ReportService` on top - `SimulationEngine` is
    constructed with the exact same `Zoo` instance `ZooService` caches
    (see `ZooService`'s docstring on why that matters).

    Args:
        database_path (str | None, optional): path to the SQLite file.
            Defaults to `database/zoo.db` relative to this package.

    Returns:
        tuple[ZooService, SimulationService, ReportService]: ready to
        pass straight into `ZooController.__init__()`.

    Test:
        - Given a database_path pointing to a non-existent file, when
          `_build_default_dependencies()` is called, then the file is
          created, a zoo is seeded, and the returned ZooService's
          `get_zoo()` returns a Zoo with 3 Enclosures.
        - Given `_build_default_dependencies()` was already called once
          for the same database_path (so a zoo already exists), when
          called again, then it reuses the existing zoo instead of
          seeding a second one.
    """
    from zoo_simulation.database.database_connection import SQLiteConnection
    from zoo_simulation.repositories.sqlite.sqlite_animal_repository import SQLAnimalRepository
    from zoo_simulation.repositories.sqlite.sqlite_employee_repository import SQLEmployeeRepository
    from zoo_simulation.repositories.sqlite.sqlite_enclosure_repository import SQLEnclosureRepository
    from zoo_simulation.repositories.sqlite.sqlite_finance_repository import SQLFinanceRepository
    from zoo_simulation.repositories.sqlite.sqlite_inventory_repository import SQLInventoryRepository
    from zoo_simulation.repositories.sqlite.sqlite_zoo_repository import SQLZooRepository
    from zoo_simulation.services.report_service import ReportService
    from zoo_simulation.services.simulation_service import SimulationService
    from zoo_simulation.services.zoo_service import ZooService
    from zoo_simulation.simulation.simulation_engine import SimulationEngine

    path = database_path or _DEFAULT_DATABASE_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    connection = SQLiteConnection(path)
    connection.connect()
    _apply_schema(connection)

    finance_repository = SQLFinanceRepository(connection)
    inventory_repository = SQLInventoryRepository(connection)
    enclosure_repository = SQLEnclosureRepository(connection)
    animal_repository = SQLAnimalRepository(connection)
    employee_repository = SQLEmployeeRepository(connection, finance_repository)
    zoo_repository = SQLZooRepository(
        connection, enclosure_repository, inventory_repository, finance_repository, employee_repository
    )

    existing_zoo_row = connection.execute("SELECT zoo_id FROM zoo LIMIT 1").fetchone()
    zoo_id = (
        existing_zoo_row["zoo_id"]
        if existing_zoo_row is not None
        else _seed_initial_zoo(connection, enclosure_repository, inventory_repository, employee_repository)
    )

    zoo_service = ZooService(
        zoo_id,
        zoo_repository,
        animal_repository,
        enclosure_repository,
        employee_repository,
        inventory_repository,
        finance_repository,
    )
    simulation_engine = SimulationEngine(zoo_service.get_zoo())
    simulation_service = SimulationService(simulation_engine)
    report_service = ReportService(animal_repository, finance_repository, inventory_repository)

    return zoo_service, simulation_service, report_service


class ZooController:
    """ZooController - the single entry point the Flask frontend calls into.

    Translates between the frontend's plain dict/primitive requests and
    the service layer's domain objects, and back into the uniform result
    dict `{"success": bool, "message": str, "data": Any}` (agreed with
    the Frontend focus, see planning_backend_darnell.md section 2.1) so
    ZooView never has to touch ZooService/domain objects directly.

    `zoo_view.py` instantiates its controller with zero arguments
    (`_controller = ZooController()`, see that module's docstring: "Der
    Tausch auf die echte Implementierung passiert an genau einer Stelle
    (dem Import unten)" - swapping the `MockZooController` import for
    this class is meant to be the *only* change needed there). Since
    that instantiation happens at blueprint-import time, before any
    dedicated composition-root code could run, this class supports
    building its own dependencies when none are supplied
    (`_build_default_dependencies()`) - a real SQLite-backed
    ZooService/SimulationService/ReportService, self-seeded with a
    starter zoo on first run. Explicit constructor injection (passing
    all three services directly) remains available and is what every
    test in this module uses - the zero-argument path exists
    specifically for `zoo_view.py`'s constraint, not to replace normal
    dependency injection.

        - Constructor: stores the three services privately.
        - _zoo_service (ZooService), _simulation_service
          (SimulationService), _report_service (ReportService).
    """

    def __init__(
        self,
        zoo_service: ZooService | None = None,
        simulation_service: SimulationService | None = None,
        report_service: ReportService | None = None,
        database_path: str | None = None,
    ) -> None:
        """Store the services this controller mediates between.

        Args:
            zoo_service (ZooService | None, optional): zoo management
                business logic. Defaults to None.
            simulation_service (SimulationService | None, optional):
                simulation stepping. Defaults to None.
            report_service (ReportService | None, optional): report
                generation/export (Database focus). Defaults to None.
            database_path (str | None, optional): only used when
                self-wiring (see class docstring) - path to the SQLite
                file to connect to/initialize. Defaults to
                `database/zoo.db` relative to this package. Ignored if
                `zoo_service`/`simulation_service`/`report_service` are
                all supplied.

        Test:
            - Given the three services, when ZooController is
              constructed, then every method can be called immediately
              without further setup, using exactly those instances.
            - Given no arguments at all, when ZooController is
              constructed, then it self-wires a real SQLite-backed
              ZooService/SimulationService/ReportService and every
              method can still be called immediately.
        """
        if zoo_service is None or simulation_service is None or report_service is None:
            zoo_service, simulation_service, report_service = _build_default_dependencies(database_path)
        self._zoo_service = zoo_service
        self._simulation_service = simulation_service
        self._report_service = report_service

    def show_status(self) -> dict[str, Any]:
        """Report the current zoo status: visitors, enclosures, animals, finances.

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            On success, `data` matches `controller_stub.py`'s
            `MockZooController.show_status()` contract exactly (the
            frontend's established, already-merged interface - see
            `zoo_view.py`'s `show_zoo_status()`/`show_animals()`) so this
            method is a drop-in replacement:
            `zoo` (flat dict of id/name/location/current_visitors/
            maximum_visitors), `animals` (`pandas.DataFrame`, one row per
            animal with columns id/name/species/age/health/hunger/energy/
            enclosure_id), `enclosures` (`pandas.DataFrame`, one row per
            enclosure with columns id/name/enclosure_type/capacity/
            cleanliness/temperature - `cleanliness` converted from the
            domain's 0-100 scale to the frontend's established 0-1
            fraction), `simulation_time` (int), `balance` (float),
            `food_catalog` (list of `{"id", "name", "price_per_unit"}`,
            built from the zoo's Inventory FoodItems, ignoring any
            Medications it also holds) and `employees` (list of
            `{"id", "name", "role", "salary"}`, added 2026-08-09
            alongside `hire_employee()`/`clean_enclosure()` - not part
            of `controller_stub.py`'s original contract, a pure
            addition).

        Test:
            - Given a zoo with 1 enclosure and 2 animals, when
              `show_status()` is called, then `success` is True and
              `data["animals"]` has 2 rows, both with that enclosure's id
              in their `enclosure_id` column.
            - Given the managed zoo cannot be loaded (e.g. misconfigured
              zoo_id), when `show_status()` is called, then `success` is
              False and `message` describes the error.
        """
        try:
            zoo = self._zoo_service.get_zoo()
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}

        animal_rows = [
            {
                "id": animal.id,
                "name": animal.name,
                "species": animal.species,
                "age": animal.age,
                "health": animal.health,
                "hunger": animal.hunger,
                "energy": animal.energy,
                "enclosure_id": enclosure.id,
            }
            for enclosure in zoo.enclosures
            for animal in enclosure.animals
        ]
        enclosure_rows = [
            {
                "id": enclosure.id,
                "name": enclosure.name,
                "enclosure_type": enclosure.enclosure_type,
                "capacity": enclosure.capacity,
                "cleanliness": enclosure.cleanliness / _CLEANLINESS_FRACTION_DIVISOR,
                "temperature": enclosure.temperature,
            }
            for enclosure in zoo.enclosures
        ]
        food_catalog = [
            {"id": item.id, "name": item.name, "price_per_unit": item.price_per_unit}
            for item in zoo.inventory.items
            if isinstance(item, FoodItem)
        ]
        medication_catalog = [
            {"id": item.id, "name": item.name}
            for item in zoo.inventory.items
            if isinstance(item, Medication)
        ]
        employees = [
            {"id": employee.id, "name": employee.name, "role": type(employee).__name__, "salary": employee.salary}
            for employee in zoo.employees
        ]

        return {
            "success": True,
            "message": "Zoo status loaded.",
            "data": {
                "zoo": {
                    "id": zoo.id,
                    "name": zoo.name,
                    "location": zoo.location,
                    "current_visitors": zoo.current_visitors,
                    "maximum_visitors": zoo.maximum_visitors,
                },
                "animals": pd.DataFrame(animal_rows),
                "enclosures": pd.DataFrame(enclosure_rows),
                "simulation_time": self._simulation_service.get_simulation_time(),
                "balance": zoo.finance_manager.get_balance(),
                "food_catalog": food_catalog,
                "medication_catalog": medication_catalog,
                "employees": employees,
            },
        }

    def add_animal(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add a new animal from frontend-supplied request data.

        Args:
            data (dict): expected keys `"species"` ("Lion"/"Giraffe"/
                "Penguin"), `"name"` (str) and `"enclosure_id"` (int).
                Optional: `"food_preference"`, `"age"`, `"health"`,
                `"hunger"`, `"energy"` (Animal's own constructor defaults
                apply if omitted). Shape validation (required fields
                present, correct types) is Flask's responsibility - this
                method validates domain rules only (species known,
                enclosure exists and has room).

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            On success, `data` contains the new animal's `id`
            (`ZooService.add_animal()`'s return value) plus `name`/
            `species`/`enclosure_id` - `zoo_view.py`'s
            `handle_add_animal_form()` reads `data["id"]` to highlight
            the newly added animal after redirecting, matching
            `controller_stub.py`'s established contract.

        Test:
            - Given data={"species": "Lion", "name": "Simba",
              "enclosure_id": 1} and enclosure 1 has free capacity, when
              `add_animal(data)` is called, then `success` is True and
              `data["id"]` is a positive int.
            - Given data with an unknown species (e.g. "Elephant"), when
              `add_animal(data)` is called, then `success` is False and
              no animal is persisted.
        """
        try:
            species = data["species"]
            animal_class = _SPECIES_TO_CLASS.get(species)
            if animal_class is None:
                raise ValueError(f"Unknown species: {species!r}")

            name = data["name"]
            # int(...) guards against e.g. a numpy.int64 sneaking in from
            # a DataFrame-derived caller - sqlite3 silently mis-binds
            # those, breaking FOREIGN KEY checks (found while wiring
            # this against a real SQLite database).
            enclosure_id = int(data["enclosure_id"])
            food_preference = data.get("food_preference", _DEFAULT_FOOD_PREFERENCE[species])

            kwargs: dict[str, Any] = {
                "name": name,
                "behaviors": _default_behaviors(food_preference),
                "food_preference": food_preference,
            }
            for stat in ("age", "health", "hunger", "energy"):
                if stat in data:
                    kwargs[stat] = data[stat]

            animal = animal_class(**kwargs)
            new_id = self._zoo_service.add_animal(animal, enclosure_id)
        except KeyError as exc:
            return {"success": False, "message": f"Missing required field: {exc}", "data": None}
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}

        return {
            "success": True,
            "message": f"{name} was added to enclosure {enclosure_id}.",
            "data": {"id": new_id, "name": name, "species": species, "enclosure_id": enclosure_id},
        }

    def feed_animal(self, animal_id: int, food_id: int) -> dict[str, Any]:
        """Feed a stored animal with a stored food item.

        Args:
            animal_id (int): id of the animal to feed.
            food_id (int): id of the FoodItem to feed it with.

        Returns:
            dict: `{"success": bool, "message": str, "data": None}`.

        Test:
            - Given an existing animal and available food, when
              `feed_animal(animal_id, food_id)` is called, then
              `success` is True.
            - Given an animal_id that does not exist, when
              `feed_animal()` is called, then `success` is False and
              `message` describes the error.
        """
        try:
            self._zoo_service.feed_animal(animal_id, food_id)
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}
        return {"success": True, "message": "Animal fed.", "data": None}

    def treat_animal(self, animal_id: int, medication_id: int) -> dict[str, Any]:
        """Treat a stored animal with a stored medication.

        Added 2026-08-09: not part of the original `ZooController`
        diagram - the frontend's "Behandeln" button was a disabled
        placeholder ("Tierarzt-Funktion existiert im Backend noch
        nicht") until now (see `planning_backend_darnell.md` section
        2.10).

        Args:
            animal_id (int): id of the animal to treat.
            medication_id (int): id of the Medication to use.

        Returns:
            dict: `{"success": bool, "message": str, "data": None}`.

        Test:
            - Given an existing animal, available medication and an
              employed Veterinarian, when
              `treat_animal(animal_id, medication_id)` is called, then
              `success` is True.
            - Given the zoo employs no Veterinarian, when
              `treat_animal()` is called, then `success` is False.
        """
        try:
            self._zoo_service.treat_animal(animal_id, medication_id)
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}
        return {"success": True, "message": "Animal treated.", "data": None}

    def sell_ticket(self, price: float) -> dict[str, Any]:
        """Sell one visitor ticket.

        Args:
            price (float): ticket price.

        Returns:
            dict: `{"success": bool, "message": str, "data": None}`.

        Test:
            - Given the zoo has room for more visitors, when
              `sell_ticket(15.0)` is called, then `success` is True.
            - Given the zoo is at maximum visitor capacity, when
              `sell_ticket()` is called, then `success` is False and no
              income is recorded.
        """
        try:
            self._zoo_service.sell_ticket(price)
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}
        return {"success": True, "message": "Ticket sold.", "data": None}

    def hire_employee(self, data: dict[str, Any]) -> dict[str, Any]:
        """Hire a new employee from frontend-supplied request data.

        Added 2026-08-09: not part of the original `ZooController`
        diagram, which had no employee-management entry point at all -
        `ZooService.hire_employee()` already existed but nothing above
        it ever called it (see `planning_backend_darnell.md` section
        2.9 for the full rationale).

        Args:
            data (dict): expected keys `"role"` ("Zookeeper"/
                "Veterinarian"/"Administrator"), `"name"` (str).
                Optional: `"salary"` (defaults to 0.0). Shape validation
                is Flask's responsibility - this method validates domain
                rules only (role known).

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            On success, `data` contains `name`/`role`/`salary`.

        Test:
            - Given data={"role": "Zookeeper", "name": "Alex", "salary":
              2000.0}, when `hire_employee(data)` is called, then
              `success` is True and the employee is persisted via
              `ZooService.hire_employee()`.
            - Given data with an unknown role (e.g. "Cleaner"), when
              `hire_employee(data)` is called, then `success` is False
              and nothing is persisted.
        """
        try:
            role = data["role"]
            employee_class = _ROLE_TO_CLASS.get(role)
            if employee_class is None:
                raise ValueError(f"Unknown role: {role!r}")

            name = data["name"]
            salary = float(data.get("salary", 0.0))

            if employee_class is Administrator:
                finance_manager = self._zoo_service.get_zoo().finance_manager
                employee = Administrator(name, finance_manager, salary=salary)
            else:
                employee = employee_class(name, salary=salary)

            self._zoo_service.hire_employee(employee)
        except KeyError as exc:
            return {"success": False, "message": f"Missing required field: {exc}", "data": None}
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}

        return {
            "success": True,
            "message": f"{name} was hired as {role}.",
            "data": {"name": name, "role": role, "salary": salary},
        }

    def clean_enclosure(self, enclosure_id: int) -> dict[str, Any]:
        """Clean a stored enclosure, resetting its cleanliness to maximum.

        Added 2026-08-09: not part of the original `ZooController`
        diagram - `Enclosure.clean()`/`Zookeeper.clean_enclosure()`
        existed in the domain model, but nothing above the domain layer
        ever called them (see `planning_backend_darnell.md` section 2.9
        for the full rationale).

        Args:
            enclosure_id (int): id of the enclosure to clean.

        Returns:
            dict: `{"success": bool, "message": str, "data": None}`.

        Test:
            - Given an existing enclosure, when
              `clean_enclosure(enclosure_id)` is called, then `success`
              is True and that enclosure's cleanliness is reset to
              maximum.
            - Given an enclosure_id that does not exist, when
              `clean_enclosure()` is called, then `success` is False.
        """
        try:
            self._zoo_service.clean_enclosure(int(enclosure_id))
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}
        return {"success": True, "message": "Enclosure cleaned.", "data": None}

    def run_simulation_step(self) -> dict[str, Any]:
        """Advance the simulation by one tick.

        Returns:
            dict: `{"success": True, "message": str, "data": {"simulation_time": int}}`.
            `run_step()`/`SimulationEngine.tick()` raise no expected
            domain errors, so this method never reports `success: False`.

        Test:
            - Given simulation_time=2, when `run_simulation_step()` is
              called, then `data["simulation_time"]` is 3.
            - When called twice in a row, then `data["simulation_time"]`
              increases by 1 each time (no steps are skipped or
              double-counted).
        """
        self._simulation_service.run_step()
        return {
            "success": True,
            "message": "Simulation advanced by 1 step.",
            "data": {"simulation_time": self._simulation_service.get_simulation_time()},
        }

    def create_report(self, format: str | None = None) -> dict[str, Any]:
        """Build the financial report, optionally as a downloadable file.

        Matches the `GET /reports/financial` route (see
        planning_frontend_alessio.md's route table). For `format` in
        (`None`, `"html"`), `data` carries `"report"` (the raw
        transactions DataFrame) and `"balance"` (float, from the zoo's
        FinanceManager) for an in-page table - matching
        `controller_stub.py`'s established contract exactly (see
        `zoo_view.py`'s `show_financial_report()`, which reads both
        keys). For `"csv"`/`"xlsx"`, a temporary file is written via
        `ReportService.export_csv()`/`export_excel()` and `data` carries
        `{"file_path": str, "mimetype": str}` so the Flask route can
        stream it back via `send_file()`.

        Args:
            format (str | None, optional): `None`/`"html"`, `"csv"` or
                `"xlsx"`. Defaults to None.

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            `success` is False for an unsupported format, without
            writing any file.

        Test:
            - Given `format=None`, when `create_report()` is called,
              then `success` is True, `data["report"]` is a DataFrame
              and `data["balance"]` is a float.
            - Given `format="csv"`, when `create_report("csv")` is
              called, then `success` is True, `data["file_path"]` points
              to an existing `.csv` file and `data["mimetype"]` is
              "text/csv".
            - Given `format="pdf"` (unsupported), when
              `create_report("pdf")` is called, then `success` is False,
              `data` is None, and no file is written.
        """
        report = self._report_service.create_financial_report()

        if format in (None, "html"):
            try:
                balance = self._zoo_service.get_zoo().finance_manager.get_balance()
            except ValueError:
                balance = 0.0
            return {
                "success": True,
                "message": "Financial report generated.",
                "data": {"report": report, "balance": balance},
            }

        if format not in ("csv", "xlsx"):
            return {
                "success": False,
                "message": f"Unsupported report format: {format!r}.",
                "data": None,
            }

        suffix = ".csv" if format == "csv" else ".xlsx"
        tmp_file = tempfile.NamedTemporaryFile(prefix="financial_report_", suffix=suffix, delete=False)
        tmp_path = Path(tmp_file.name)
        tmp_file.close()

        if format == "csv":
            self._report_service.export_csv(report, str(tmp_path))
            mimetype = _CSV_MIMETYPE
        else:
            self._report_service.export_excel(report, str(tmp_path))
            mimetype = _XLSX_MIMETYPE

        return {
            "success": True,
            "message": f"Financial report exported as {format}.",
            "data": {"file_path": str(tmp_path), "mimetype": mimetype},
        }
