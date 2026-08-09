"""ZooController: mediates between the Flask frontend (Alessio) and the service layer.

Schwerpunkt: Backend (Controller Layer) - Darnell Beganovic
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from zoo_simulation.domain.animals.giraffe import Giraffe
from zoo_simulation.domain.animals.lion import Lion
from zoo_simulation.domain.animals.penguin import Penguin
from zoo_simulation.domain.behaviors.feeding_behavior import FeedingBehavior
from zoo_simulation.domain.behaviors.rest_behavior import RestBehavior
from zoo_simulation.domain.behaviors.social_behavior import SocialBehavior

if TYPE_CHECKING:
    from zoo_simulation.domain.behaviors.behavior import Behavior
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

_CSV_MIMETYPE = "text/csv"
_XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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


class ZooController:
    """ZooController - the single entry point the Flask frontend calls into.

    Translates between the frontend's plain dict/primitive requests and
    the service layer's domain objects, and back into the uniform result
    dict `{"success": bool, "message": str, "data": Any}` (agreed with
    the Frontend focus, see planning_backend_darnell.md section 2.1) so
    ZooView never has to touch ZooService/domain objects directly.

    Deliberately does not construct its own ZooService/
    SimulationService/ReportService - those, and any concrete
    repository/DatabaseConnection wiring, are assembled elsewhere (a
    dedicated composition-root/integration step, still pending - see
    main.py).

        - Constructor: stores the three services privately.
        - _zoo_service (ZooService), _simulation_service
          (SimulationService), _report_service (ReportService).
    """

    def __init__(
        self,
        zoo_service: ZooService,
        simulation_service: SimulationService,
        report_service: ReportService,
    ) -> None:
        """Store the services this controller mediates between.

        Args:
            zoo_service (ZooService): zoo management business logic.
            simulation_service (SimulationService): simulation stepping.
            report_service (ReportService): report generation/export
                (Database focus).

        Test:
            - Given the three services, when ZooController is
              constructed, then every method can be called immediately
              without further setup.
            - Given service doubles instead of the real services, when
              ZooController is used, then it works identically, since it
              only calls their public methods.
        """
        self._zoo_service = zoo_service
        self._simulation_service = simulation_service
        self._report_service = report_service

    def show_status(self) -> dict[str, Any]:
        """Report the current zoo status: visitors, enclosures, animals, finances.

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            On success, `data` contains `zoo` (dict of id/name/location/
            current_visitors/maximum_visitors), `enclosures` (list of
            dicts, each with its animals as a list of dicts),
            `average_welfare` (float), `balance` (float) and
            `simulation_time` (int). This shape is a Backend-side default
            - aligning it 1:1 with the frontend's `MockZooController`
            stub shape is part of the future integration step, not done
            here.

        Test:
            - Given a zoo with 1 enclosure and 2 animals, when
              `show_status()` is called, then `success` is True and
              `data["enclosures"]` has length 1 with 2 entries in its
              `animals` list.
            - Given the managed zoo cannot be loaded (e.g. misconfigured
              zoo_id), when `show_status()` is called, then `success` is
              False and `message` describes the error.
        """
        try:
            zoo = self._zoo_service.get_zoo()
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}

        enclosures = [
            {
                "id": enclosure.id,
                "name": enclosure.name,
                "enclosure_type": enclosure.enclosure_type,
                "capacity": enclosure.capacity,
                "cleanliness": enclosure.cleanliness,
                "temperature": enclosure.temperature,
                "animals": [
                    {
                        "id": animal.id,
                        "name": animal.name,
                        "species": animal.species,
                        "age": animal.age,
                        "health": animal.health,
                        "hunger": animal.hunger,
                        "energy": animal.energy,
                    }
                    for animal in enclosure.animals
                ],
            }
            for enclosure in zoo.enclosures
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
                "enclosures": enclosures,
                "average_welfare": zoo.calculate_average_welfare(),
                "balance": zoo.finance_manager.get_balance(),
                "simulation_time": self._simulation_service.get_simulation_time(),
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

        Test:
            - Given data={"species": "Lion", "name": "Simba",
              "enclosure_id": 1} and enclosure 1 has free capacity, when
              `add_animal(data)` is called, then `success` is True and
              the animal is persisted via `ZooService.add_animal()`.
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
            enclosure_id = data["enclosure_id"]
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
            self._zoo_service.add_animal(animal, enclosure_id)
        except KeyError as exc:
            return {"success": False, "message": f"Missing required field: {exc}", "data": None}
        except ValueError as exc:
            return {"success": False, "message": str(exc), "data": None}

        return {
            "success": True,
            "message": f"{name} was added to enclosure {enclosure_id}.",
            "data": {"name": name, "species": species, "enclosure_id": enclosure_id},
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
        (`None`, `"html"`), `data["report"]` carries the raw DataFrame
        for an in-page table. For `"csv"`/`"xlsx"`, a temporary file is
        written via `ReportService.export_csv()`/`export_excel()` and
        `data` carries `{"file_path": str, "mimetype": str}` so the
        Flask route can stream it back via `send_file()`.

        Args:
            format (str | None, optional): `None`/`"html"`, `"csv"` or
                `"xlsx"`. Defaults to None.

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            `success` is False for an unsupported format, without
            writing any file.

        Test:
            - Given `format=None`, when `create_report()` is called,
              then `success` is True and `data["report"]` is a
              DataFrame.
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
            return {
                "success": True,
                "message": "Financial report generated.",
                "data": {"report": report},
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
