"""ZooService: application/business logic coordinating the domain model and repositories.

Schwerpunkt: Backend (Service Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.food_item import FoodItem

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal
    from zoo_simulation.domain.employees.employee import Employee
    from zoo_simulation.domain.zoo import Zoo
    from zoo_simulation.repositories.interfaces.animal_repository import AnimalRepository
    from zoo_simulation.repositories.interfaces.employee_repository import EmployeeRepository
    from zoo_simulation.repositories.interfaces.enclosure_repository import EnclosureRepository
    from zoo_simulation.repositories.interfaces.finance_repository import FinanceRepository
    from zoo_simulation.repositories.interfaces.inventory_repository import InventoryRepository
    from zoo_simulation.repositories.interfaces.zoo_repository import ZooRepository


class ZooService:
    """ZooService - business logic for zoo management, on top of the repository interfaces.

    Depends only on the six repository *interfaces* (Dependency
    Inversion Principle) - never on a concrete SQLite implementation.
    Validates domain rules (e.g. enclosure capacity, unknown ids); Flask
    (Frontend focus) is responsible for validating request *shape*
    before calling this service (see
    planning_backend_darnell.md section 5). Scoped to a single zoo per
    the project's single-zoo assumption (see planning_db_kaiss.md) -
    `zoo_id` is fixed at construction, not passed per call.

    Deliberately does not itself construct/wire concrete
    SQL*Repository/DatabaseConnection instances - that composition-root
    wiring lives in `zoo_controller.py`'s default-construction path (see
    `main.py`).

    `get_zoo()` loads the managed Zoo aggregate once and caches that
    exact instance for the service's lifetime (added 2026-08-09 while
    wiring `SimulationEngine`): the two are constructed with the very
    same `Zoo` object in the composition root, so `SimulationEngine`
    always ticks against whatever `ZooService` currently has in memory,
    instead of a stale snapshot from startup. Every mutating method
    therefore updates this cached object's in-memory graph *and*
    persists via the repositories - not just one or the other - so
    reads (`get_zoo()`, and by extension `SimulationEngine`) stay
    consistent with what was just written. Simulation tick effects
    themselves (hunger/energy/age/cleanliness changes, salary
    transactions) are intentionally NOT persisted back to the database
    by this class - see `SimulationEngine`'s own docstring for that
    documented limitation.

        - Constructor: stores all repository interfaces and the managed
          `zoo_id` privately.
        - _zoo_id (int): id of the one Zoo this service manages.
        - _zoo_repository (ZooRepository), _animal_repository
          (AnimalRepository), _enclosure_repository (EnclosureRepository),
          _employee_repository (EmployeeRepository), _inventory_repository
          (InventoryRepository), _finance_repository (FinanceRepository).
        - _zoo_cache (Zoo | None): lazily loaded by `get_zoo()`, then
          reused for the rest of this service's lifetime.
    """

    def __init__(
        self,
        zoo_id: int,
        zoo_repository: ZooRepository,
        animal_repository: AnimalRepository,
        enclosure_repository: EnclosureRepository,
        employee_repository: EmployeeRepository,
        inventory_repository: InventoryRepository,
        finance_repository: FinanceRepository,
    ) -> None:
        """Store the managed zoo's id and the repository interfaces used to serve it.

        Args:
            zoo_id (int): id of the one Zoo this service manages.
            zoo_repository (ZooRepository): persistence for the Zoo
                aggregate itself.
            animal_repository (AnimalRepository): persistence for
                Animals.
            enclosure_repository (EnclosureRepository): persistence for
                Enclosures.
            employee_repository (EmployeeRepository): persistence for
                Employees.
            inventory_repository (InventoryRepository): persistence for
                FoodItem/Medication stock.
            finance_repository (FinanceRepository): persistence for
                Transactions.

        Test:
            - Given a zoo_id and six repository doubles (e.g. fakes in a
              test), when ZooService is constructed, then
              `get_zoo()`/`add_animal()`/etc. can be called immediately.
            - Given repository doubles instead of real SQL*Repository
              instances, when ZooService is used, then it works
              identically, since it only depends on the interfaces.
        """
        self._zoo_id = zoo_id
        self._zoo_repository = zoo_repository
        self._animal_repository = animal_repository
        self._enclosure_repository = enclosure_repository
        self._employee_repository = employee_repository
        self._inventory_repository = inventory_repository
        self._finance_repository = finance_repository
        self._zoo_cache: Zoo | None = None

    def get_zoo(self) -> Zoo:
        """Load the managed Zoo aggregate, caching it for subsequent calls.

        Returns:
            Zoo: the zoo this service manages - the same instance on
                every call after the first (see class docstring).

        Raises:
            ValueError: if the managed `zoo_id` does not exist in
                storage - a configuration error (the service was set up
                with a wrong id), not a normal runtime case.

        Test:
            - Given a stored Zoo matching the managed zoo_id, when
              `get_zoo()` is called, then the returned Zoo's `.id`
              matches it.
            - Given `get_zoo()` was already called once successfully,
              when it is called again, then the exact same Zoo instance
              is returned (no second repository lookup).
        """
        if self._zoo_cache is None:
            zoo = self._zoo_repository.get_by_id(self._zoo_id)
            if zoo is None:
                raise ValueError(f"Zoo {self._zoo_id} not found.")
            self._zoo_cache = zoo
        return self._zoo_cache

    def add_animal(self, animal: Animal, enclosure_id: int) -> int:
        """Add a new animal to an existing enclosure, if it has room.

        Args:
            animal (Animal): the animal to add (not yet persisted).
            enclosure_id (int): id of the enclosure to house it in.

        Returns:
            int: the new animal's id (`AnimalRepository.save()`'s return
                value). Added 2026-08-09 while wiring `ZooController`:
                the frontend's "adopt animal" flow needs the new id
                back to highlight the animal after redirecting (see
                `zoo_view.py`'s `handle_add_animal_form()`) - a diagram
                deviation from `void`, same pattern as the repository
                layer's `save()` methods.

        Raises:
            ValueError: if `enclosure_id` does not exist, or the
                enclosure is already at full capacity.

        Test:
            - Given an existing enclosure with free capacity, when
              `add_animal(animal, enclosure_id)` is called, then the
              returned id is a positive int, the animal is persisted via
              AnimalRepository.save() with that enclosure_id, and
              `get_zoo()`'s matching enclosure now includes it.
            - Given an enclosure_id that does not exist, when
              `add_animal()` is called, then a ValueError is raised and
              nothing is persisted.
        """
        zoo = self.get_zoo()
        enclosure = next((e for e in zoo.enclosures if e.id == enclosure_id), None)
        if enclosure is None:
            raise ValueError(f"Enclosure {enclosure_id} not found.")
        if not enclosure.has_capacity():
            raise ValueError(f"Enclosure {enclosure_id} is at full capacity.")

        new_id = self._animal_repository.save(animal, enclosure_id)
        # animal.id is None (read-only, never settable) - re-fetch so the
        # cached Zoo's graph holds a correctly-identified instance,
        # consistent with every other animal loaded via the repository.
        enclosure.add_animal(self._animal_repository.get_by_id(new_id))
        return new_id

    def feed_animal(self, animal_id: int, food_id: int) -> None:
        """Feed a stored animal with a stored food item.

        Args:
            animal_id (int): id of the animal to feed.
            food_id (int): id of the FoodItem to feed it with.

        Raises:
            ValueError: if `animal_id` or `food_id` does not exist.

        Test:
            - Given an animal with hunger=80 and available food, when
              `feed_animal(animal_id, food_id)` is called, then hunger
              decreases and the food's stored quantity decreases by the
              expected amount, visible both via `get_zoo()` and in
              storage.
            - Given an animal id that does not exist, when
              `feed_animal()` is called, then a ValueError is raised and
              no inventory change occurs.
        """
        zoo = self.get_zoo()
        animal = next(
            (a for enclosure in zoo.enclosures for a in enclosure.animals if a.id == animal_id), None
        )
        if animal is None:
            raise ValueError(f"Animal {animal_id} not found.")
        food = next(
            (item for item in zoo.inventory.items if item.id == food_id and isinstance(item, FoodItem)),
            None,
        )
        if food is None:
            raise ValueError(f"FoodItem {food_id} not found.")

        animal.eat(food)

        self._animal_repository.update(animal)
        self._inventory_repository.update_item(food)

    def hire_employee(self, employee: Employee) -> None:
        """Hire a new employee for the managed zoo.

        Args:
            employee (Employee): the employee to hire (not yet
                persisted).

        Test:
            - Given a new Zookeeper instance, when `hire_employee()` is
              called, then it is persisted via EmployeeRepository.save()
              for the managed zoo_id and appears in `get_zoo().employees`
              afterward.
            - Given two different Employee instances, when
              `hire_employee()` is called for each, then both are
              persisted as separate rows.
        """
        new_id = self._employee_repository.save(employee, self._zoo_id)
        # employee.id is None (read-only, never settable) - re-fetch for
        # the same reason as add_animal().
        self.get_zoo().add_employee(self._employee_repository.get_by_id(new_id))

    def sell_ticket(self, price: float) -> None:
        """Sell one visitor ticket, if the zoo has not reached capacity.

        Registers the visitor (`Zoo.register_visitor()`), persists the
        updated visitor count, and records the sale as income via the
        zoo's FinanceManager.

        Args:
            price (float): ticket price, must be positive (see
                `FinanceManager.record_income()`).

        Raises:
            ValueError: if the zoo is at `maximum_visitors` capacity, or
                `price` is not positive.

        Test:
            - Given current_visitors < maximum_visitors, when
              `sell_ticket(15.0)` is called, then the zoo's visitor count
              increases by 1 and the FinanceManager's balance increases
              by 15.0.
            - Given current_visitors == maximum_visitors, when
              `sell_ticket()` is called, then a ValueError is raised and
              no income is recorded.
        """
        zoo = self.get_zoo()
        if not zoo.register_visitor():
            raise ValueError("Zoo is at maximum visitor capacity.")
        self._zoo_repository.update(zoo)

        transaction = zoo.finance_manager.record_income(price, "Ticket sale")
        self._finance_repository.save_transaction(transaction, self._zoo_id)
