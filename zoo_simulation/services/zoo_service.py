"""ZooService: application/business logic coordinating the domain model and repositories.

Schwerpunkt: Backend (Service Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.employees.administrator import Administrator
from zoo_simulation.domain.employees.veterinarian import Veterinarian
from zoo_simulation.domain.employees.zookeeper import Zookeeper
from zoo_simulation.domain.food_item import FoodItem
from zoo_simulation.domain.medication import Medication

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
            # Added 2026-08-09 (see planning_backend_darnell.md section
            # 2.11 and planning_db_kaiss.md section 6): a freshly
            # reconstructed Administrator carries its own separate
            # FinanceManager, not `zoo.finance_manager` - pointing it at
            # the Zoo's canonical one here, once per cache-fill, keeps
            # `_record_income()`/`_record_expense()`'s bookkeeping
            # visible via `zoo.finance_manager.get_balance()`.
            for employee in zoo.employees:
                if isinstance(employee, Administrator):
                    employee.set_finance_manager(zoo.finance_manager)
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

    def remove_animal(self, animal_id: int) -> None:
        """Remove a stored animal permanently.

        Added 2026-08-09 (see planning_backend_darnell.md section 2.11):
        `AnimalRepository.delete()` existed since the Database focus's
        original interface but nothing above it ever called it - there
        was no removal entry point at all, only `add_animal()`.

        Persists the deletion first, then updates the cached Zoo's
        in-memory graph (`Enclosure.remove_animal()`) - same ordering as
        `add_animal()`, so a read via `get_zoo()` right after this call
        never observes a stale, already-deleted animal.

        Args:
            animal_id (int): id of the animal to remove.

        Raises:
            ValueError: if `animal_id` does not exist.

        Test:
            - Given an existing animal housed in an enclosure, when
              `remove_animal(animal_id)` is called, then it no longer
              appears in that enclosure's `.animals` nor in storage.
            - Given an animal_id that does not exist, when
              `remove_animal()` is called, then a ValueError is raised
              and nothing is deleted.
        """
        zoo = self.get_zoo()
        enclosure = next((e for e in zoo.enclosures if any(a.id == animal_id for a in e.animals)), None)
        if enclosure is None:
            raise ValueError(f"Animal {animal_id} not found.")
        self._animal_repository.delete(animal_id)
        enclosure.remove_animal(animal_id)

    def _find_administrator(self, zoo: Zoo) -> Administrator | None:
        """Find the zoo's first employed Administrator, if any.

        Args:
            zoo (Zoo): the zoo to search.

        Returns:
            Administrator | None: the first employed Administrator, or
                None if the zoo currently employs none.

        Test:
            - Given a zoo employing one Administrator, when
              `_find_administrator(zoo)` is called, then that instance
              is returned.
            - Given a zoo employing no Administrator, when
              `_find_administrator(zoo)` is called, then None is
              returned.
        """
        return next((e for e in zoo.employees if isinstance(e, Administrator)), None)

    def _record_income(self, zoo: Zoo, amount: float, description: str) -> None:
        """Record income via the zoo's Administrator and persist the resulting Transaction.

        Added 2026-08-09 (see planning_backend_darnell.md section 2.11):
        replaces direct `zoo.finance_manager.record_income()` calls -
        `Administrator ..> FinanceManager : manages` in the class
        diagram, so bookkeeping should be routed through an employed
        Administrator, not around them.

        Args:
            zoo (Zoo): the zoo whose Administrator should record this.
            amount (float): the income amount (positive magnitude).
            description (str): human-readable note, e.g. "Ticket sale".

        Raises:
            ValueError: if the zoo employs no Administrator (per the
                explicit product decision: no silent fallback to
                FinanceManager for user-triggered income - see
                planning_backend_darnell.md section 2.11).

        Test:
            - Given a zoo employing an Administrator, when
              `_record_income(zoo, 15.0, "Ticket sale")` is called, then
              the balance increases by 15.0 and a matching Transaction
              is persisted via FinanceRepository.
            - Given a zoo employing no Administrator, when
              `_record_income()` is called, then a ValueError is raised
              and no Transaction is persisted.
        """
        administrator = self._find_administrator(zoo)
        if administrator is None:
            raise ValueError("No administrator employed to record this income.")
        transaction = administrator.record_income(amount, description)
        self._finance_repository.save_transaction(transaction, self._zoo_id)

    def _record_expense(self, zoo: Zoo, amount: float, description: str) -> None:
        """Record an expense via the zoo's Administrator and persist the resulting Transaction.

        Args:
            zoo (Zoo): the zoo whose Administrator should record this.
            amount (float): the expense amount (positive magnitude).
            description (str): human-readable note, e.g. "Feeding cost:
                Simba (Fleisch)".

        Raises:
            ValueError: if the zoo employs no Administrator - same
                policy as `_record_income()`.

        Test:
            - Given a zoo employing an Administrator, when
              `_record_expense(zoo, 24.0, "Feeding cost")` is called,
              then the balance decreases by 24.0 and a matching
              Transaction is persisted via FinanceRepository.
            - Given a zoo employing no Administrator, when
              `_record_expense()` is called, then a ValueError is raised
              and no Transaction is persisted.
        """
        administrator = self._find_administrator(zoo)
        if administrator is None:
            raise ValueError("No administrator employed to record this expense.")
        transaction = administrator.record_expense(amount, description)
        self._finance_repository.save_transaction(transaction, self._zoo_id)

    def feed_animal(self, animal_id: int, food_id: int, zookeeper_id: int) -> None:
        """Feed a stored animal with a stored food item, via a specific employed Zookeeper.

        Args:
            animal_id (int): id of the animal to feed.
            food_id (int): id of the FoodItem to feed it with.
            zookeeper_id (int): id of the employed Zookeeper who
                performs the feeding. Added 2026-08-09 (see
                planning_backend_darnell.md section 2.11) - delegates to
                `Zookeeper.feed_animal()` (previously never called by
                anything above the domain layer) instead of calling
                `Animal.eat()` directly, and requires the caller to pick
                which employed Zookeeper does it, rather than assuming
                "the first one" as `treat_animal()` originally did for
                Veterinarian.

        Raises:
            ValueError: if `animal_id`/`food_id`/`zookeeper_id` does not
                exist (or `zookeeper_id` is not a Zookeeper), or if the
                food has a positive price and the zoo employs no
                Administrator to book the resulting expense. This check
                runs before any mutation, so a rejected feed leaves the
                animal/food/finances completely unchanged (see
                `_record_expense()`'s no-silent-fallback policy).

        Test:
            - Given an animal with hunger=80, available food with
              price_per_unit=8.0, an employed Zookeeper and an employed
              Administrator, when `feed_animal(animal_id, food_id,
              zookeeper_id)` is called, then hunger decreases, the
              food's stored quantity decreases by the expected amount,
              and the zoo's FinanceManager balance decreases by
              `amount_consumed * price_per_unit`.
            - Given a zookeeper_id that is not an employed Zookeeper,
              when `feed_animal()` is called, then a ValueError is
              raised and no inventory/finance change occurs.
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
        zookeeper = next(
            (e for e in zoo.employees if e.id == zookeeper_id and isinstance(e, Zookeeper)), None
        )
        if zookeeper is None:
            raise ValueError(f"Zookeeper {zookeeper_id} not found or not employed as a Zookeeper.")
        if food.price_per_unit > 0 and self._find_administrator(zoo) is None:
            raise ValueError("No administrator employed to record this expense.")

        quantity_before = food.quantity
        zookeeper.feed_animal(animal, food)
        amount_consumed = quantity_before - food.quantity

        self._animal_repository.update(animal)
        self._inventory_repository.update_item(food)

        cost = amount_consumed * food.price_per_unit
        if cost > 0:
            self._record_expense(zoo, cost, f"Feeding cost: {animal.name} ({food.name})")

    def treat_animal(self, animal_id: int, medication_id: int, veterinarian_id: int) -> None:
        """Treat a stored animal with a stored medication, via a specific employed Veterinarian.

        Added 2026-08-09: not part of the original `ZooService` diagram
        at all - `Veterinarian.treat_animal()` existed in the domain
        model, but nothing above it was ever callable (see
        `planning_backend_darnell.md` section 2.10). Now requires the
        caller to pick which employed Veterinarian performs the
        treatment (section 2.11), rather than always using "the first
        employed Veterinarian".

        Args:
            animal_id (int): id of the animal to treat.
            medication_id (int): id of the Medication to use.
            veterinarian_id (int): id of the employed Veterinarian who
                performs the treatment.

        Raises:
            ValueError: if `animal_id`/`medication_id`/`veterinarian_id`
                does not exist, or `veterinarian_id` is not a
                Veterinarian.

        Test:
            - Given a sick animal (health=30), an existing Medication,
              and an employed Veterinarian, when
              `treat_animal(animal_id, medication_id, veterinarian_id)`
              is called, then the animal's health increases and the
              medication's stored quantity decreases, both persisted.
            - Given a veterinarian_id that is not an employed
              Veterinarian, when `treat_animal()` is called, then a
              ValueError is raised and nothing changes.
        """
        zoo = self.get_zoo()
        animal = next(
            (a for enclosure in zoo.enclosures for a in enclosure.animals if a.id == animal_id), None
        )
        if animal is None:
            raise ValueError(f"Animal {animal_id} not found.")
        medication = next(
            (item for item in zoo.inventory.items if item.id == medication_id and isinstance(item, Medication)),
            None,
        )
        if medication is None:
            raise ValueError(f"Medication {medication_id} not found.")
        veterinarian = next(
            (e for e in zoo.employees if e.id == veterinarian_id and isinstance(e, Veterinarian)), None
        )
        if veterinarian is None:
            raise ValueError(f"Veterinarian {veterinarian_id} not found or not employed as a Veterinarian.")

        veterinarian.treat_animal(animal, medication)

        self._animal_repository.update(animal)
        self._inventory_repository.update_medication(medication)

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
        zoo = self.get_zoo()
        reloaded_employee = self._employee_repository.get_by_id(new_id)
        # A freshly reloaded Administrator carries its own separate
        # FinanceManager (see get_zoo()'s docstring) - get_zoo()'s
        # cache-fill sync already ran before this employee existed, so
        # it needs the same fix-up here.
        if isinstance(reloaded_employee, Administrator):
            reloaded_employee.set_finance_manager(zoo.finance_manager)
        zoo.add_employee(reloaded_employee)

    def remove_employee(self, employee_id: int) -> None:
        """Remove a stored employee permanently.

        Added 2026-08-09 (see planning_backend_darnell.md section 2.11):
        `EmployeeRepository.delete()` existed since the Database focus's
        original interface but nothing above it ever called it - there
        was no removal entry point at all, only `hire_employee()`.
        Persists the deletion first, then updates the cached Zoo's
        in-memory graph (`Zoo.remove_employee()`), same ordering as
        `remove_animal()`.

        Args:
            employee_id (int): id of the employee to remove.

        Raises:
            ValueError: if `employee_id` does not exist.

        Test:
            - Given an existing employee, when
              `remove_employee(employee_id)` is called, then it no
              longer appears in `get_zoo().employees` nor in storage.
            - Given an employee_id that does not exist, when
              `remove_employee()` is called, then a ValueError is raised
              and nothing is deleted.
        """
        zoo = self.get_zoo()
        employee = next((e for e in zoo.employees if e.id == employee_id), None)
        if employee is None:
            raise ValueError(f"Employee {employee_id} not found.")
        self._employee_repository.delete(employee_id)
        zoo.remove_employee(employee_id)

    def clean_enclosure(self, enclosure_id: int, zookeeper_id: int) -> None:
        """Clean a stored enclosure via a specific employed Zookeeper.

        Added 2026-08-09: not part of the original `ZooService` diagram,
        which had no manual-cleaning entry point at all (see
        `planning_backend_darnell.md` section 2.9). Now requires the
        caller to pick which employed Zookeeper performs the cleaning
        (section 2.11) and delegates to `Zookeeper.clean_enclosure()`
        (previously never called by anything above the domain layer)
        instead of calling `Enclosure.clean()` directly.

        Args:
            enclosure_id (int): id of the enclosure to clean.
            zookeeper_id (int): id of the employed Zookeeper who
                performs the cleaning.

        Raises:
            ValueError: if `enclosure_id` does not exist, or
                `zookeeper_id` does not exist/is not a Zookeeper.

        Test:
            - Given an enclosure with cleanliness=40.0 and an employed
              Zookeeper, when `clean_enclosure(enclosure_id,
              zookeeper_id)` is called, then its cleanliness is 100.0,
              both via `get_zoo()` and in storage.
            - Given a zookeeper_id that is not an employed Zookeeper,
              when `clean_enclosure()` is called, then a ValueError is
              raised and the enclosure stays unchanged.
        """
        zoo = self.get_zoo()
        enclosure = next((e for e in zoo.enclosures if e.id == enclosure_id), None)
        if enclosure is None:
            raise ValueError(f"Enclosure {enclosure_id} not found.")
        zookeeper = next(
            (e for e in zoo.employees if e.id == zookeeper_id and isinstance(e, Zookeeper)), None
        )
        if zookeeper is None:
            raise ValueError(f"Zookeeper {zookeeper_id} not found or not employed as a Zookeeper.")
        zookeeper.clean_enclosure(enclosure)
        self._enclosure_repository.update(enclosure)

    def sell_ticket(self, price: float) -> None:
        """Sell one visitor ticket, if the zoo has not reached capacity.

        Registers the visitor (`Zoo.register_visitor()`), persists the
        updated visitor count, and records the sale as income via the
        zoo's employed Administrator (added 2026-08-09, see
        planning_backend_darnell.md section 2.11 - previously booked
        directly via `zoo.finance_manager`, bypassing `Administrator`
        entirely despite `Administrator ..> FinanceManager : manages`
        in the class diagram).

        Args:
            price (float): ticket price, must be positive (see
                `FinanceManager.record_income()`).

        Raises:
            ValueError: if the zoo is at `maximum_visitors` capacity,
                `price` is not positive, or the zoo employs no
                Administrator to record the income (no silent fallback
                - see `_record_income()`'s policy). The capacity/employed-
                Administrator checks run before `register_visitor()`
                mutates anything, so a rejected sale never partially
                admits a visitor without recording income.

        Test:
            - Given current_visitors < maximum_visitors and an employed
              Administrator, when `sell_ticket(15.0)` is called, then
              the zoo's visitor count increases by 1 and the
              FinanceManager's balance increases by 15.0.
            - Given the zoo employs no Administrator, when
              `sell_ticket()` is called, then a ValueError is raised and
              neither the visitor count nor the balance changes.
        """
        zoo = self.get_zoo()
        if zoo.current_visitors >= zoo.maximum_visitors:
            raise ValueError("Zoo is at maximum visitor capacity.")
        if self._find_administrator(zoo) is None:
            raise ValueError("No administrator employed to record this income.")

        zoo.register_visitor()
        self._zoo_repository.update(zoo)
        self._record_income(zoo, price, "Ticket sale")

    def add_food_item(self, food_item: FoodItem) -> int:
        """Add a brand-new FoodItem type to the zoo's Inventory.

        Added 2026-08-09 for the Inventory management tab (see
        planning_backend_darnell.md section 2.11) - `Inventory.add_item()`
        already existed but nothing above the domain layer ever created
        a persisted FoodItem beyond the one-time bootstrap seed in
        `zoo_controller.py`.

        Args:
            food_item (FoodItem): the new food type to stock (not yet
                persisted).

        Returns:
            int: the new food item's id
                (`InventoryRepository.save_item()`'s return value).

        Test:
            - Given a new FoodItem, when `add_food_item(food_item)` is
              called, then the returned id is a positive int and
              `get_zoo().inventory.items` afterward includes it.
            - Given two different FoodItems, when `add_food_item()` is
              called for each, then both are persisted as separate rows.
        """
        zoo = self.get_zoo()
        new_id = self._inventory_repository.save_item(food_item, zoo.inventory.id)
        zoo.inventory.add_item(self._inventory_repository.get_item(new_id))
        return new_id

    def add_medication(self, medication: Medication) -> int:
        """Add a brand-new Medication type to the zoo's Inventory.

        Added 2026-08-09, same rationale as `add_food_item()`.

        Args:
            medication (Medication): the new medication type to stock
                (not yet persisted).

        Returns:
            int: the new medication's id
                (`InventoryRepository.save_medication()`'s return
                value).

        Test:
            - Given a new Medication, when `add_medication(medication)`
              is called, then the returned id is a positive int and
              `get_zoo().inventory.items` afterward includes it.
            - Given two different Medications, when `add_medication()`
              is called for each, then both are persisted as separate
              rows.
        """
        zoo = self.get_zoo()
        new_id = self._inventory_repository.save_medication(medication, zoo.inventory.id)
        zoo.inventory.add_item(self._inventory_repository.get_medication(new_id))
        return new_id

    def _find_inventory_item(self, zoo: Zoo, item_id: int, is_food: bool) -> FoodItem | Medication:
        """Find a stored FoodItem/Medication by id and expected kind.

        Args:
            zoo (Zoo): the zoo whose Inventory to search.
            item_id (int): id of the item to find. Note: FoodItem and
                Medication ids come from two independent
                auto-increment sequences (separate tables, see
                `database/schema.sql`), so an id alone is ambiguous -
                `is_food` disambiguates which table/kind is meant,
                mirroring how `feed_animal()`/`treat_animal()` already
                filter `zoo.inventory.items` by `isinstance()`.
            is_food (bool): True to look for a FoodItem, False for a
                Medication.

        Returns:
            FoodItem | Medication: the matching item.

        Raises:
            ValueError: if no item of the expected kind with that id
                exists.

        Test:
            - Given a FoodItem with id=1 and a Medication with id=1
              both stocked, when `_find_inventory_item(zoo, 1,
              is_food=True)` is called, then the FoodItem is returned,
              not the Medication.
            - Given an item_id that does not exist for the requested
              kind, when `_find_inventory_item()` is called, then a
              ValueError is raised.
        """
        item_class = FoodItem if is_food else Medication
        item = next((i for i in zoo.inventory.items if i.id == item_id and isinstance(i, item_class)), None)
        if item is None:
            kind = "FoodItem" if is_food else "Medication"
            raise ValueError(f"{kind} {item_id} not found.")
        return item

    def _persist_inventory_item(self, item: FoodItem | Medication) -> None:
        """Persist an in-place update to a FoodItem/Medication.

        Args:
            item (FoodItem | Medication): the item whose quantity (or
                other attributes) changed.

        Test:
            - Given a FoodItem whose quantity changed, when
              `_persist_inventory_item(item)` is called, then
              `InventoryRepository.update_item()` is used, not
              `update_medication()`.
            - Given a Medication whose quantity changed, when
              `_persist_inventory_item(item)` is called, then
              `InventoryRepository.update_medication()` is used.
        """
        if isinstance(item, FoodItem):
            self._inventory_repository.update_item(item)
        else:
            self._inventory_repository.update_medication(item)

    def restock_inventory_item(self, item_id: int, is_food: bool, amount: float) -> None:
        """Increase a stocked FoodItem's/Medication's quantity.

        Added 2026-08-09 for the Inventory management tab (see
        planning_backend_darnell.md section 2.11).

        Args:
            item_id (int): id of the item to restock.
            is_food (bool): True for a FoodItem, False for a Medication.
            amount (float): amount to add (see
                `FoodItem.increase_quantity()`/`Medication.
                increase_quantity()` - non-positive amounts are a no-op).

        Raises:
            ValueError: if no matching item exists.

        Test:
            - Given a FoodItem with quantity=10.0, when
              `restock_inventory_item(item_id, True, 5.0)` is called,
              then its quantity is 15.0, persisted.
            - Given an item_id that does not exist for the requested
              kind, when `restock_inventory_item()` is called, then a
              ValueError is raised.
        """
        zoo = self.get_zoo()
        item = self._find_inventory_item(zoo, item_id, is_food)
        item.increase_quantity(amount)
        self._persist_inventory_item(item)

    def consume_inventory_item(self, item_id: int, is_food: bool, amount: float) -> None:
        """Manually consume some quantity of a stocked FoodItem/Medication.

        Added 2026-08-09 for the Inventory management tab (see
        planning_backend_darnell.md section 2.11) - wires
        `Inventory.consume_item()`, which existed since the domain
        model's first implementation but was never called by anything
        (feeding/treatment consume stock through `Animal.eat()`/
        `Veterinarian.treat_animal()` instead, which apply
        species/medication-specific amounts). This method is for
        manually writing off stock, e.g. spoilage or waste, independent
        of feeding/treatment.

        Args:
            item_id (int): id of the item to consume from.
            is_food (bool): True for a FoodItem, False for a Medication.
            amount (float): amount to consume, must be positive and not
                exceed current stock (see `Inventory.consume_item()`).

        Raises:
            ValueError: if no matching item exists, or stock is
                insufficient/`amount` is not positive.

        Test:
            - Given a FoodItem with quantity=10.0, when
              `consume_inventory_item(item_id, True, 4.0)` is called,
              then its quantity is 6.0, persisted.
            - Given `amount` exceeding current stock, when
              `consume_inventory_item()` is called, then a ValueError is
              raised and the quantity stays unchanged.
        """
        zoo = self.get_zoo()
        item = self._find_inventory_item(zoo, item_id, is_food)
        if not zoo.inventory.consume_item(item_id, amount):
            raise ValueError(f"Could not consume {amount} of item {item_id} (insufficient stock).")
        self._persist_inventory_item(item)

    def remove_inventory_item(self, item_id: int, is_food: bool) -> None:
        """Remove a FoodItem/Medication type from the Inventory entirely.

        Added 2026-08-09 for the Inventory management tab (see
        planning_backend_darnell.md section 2.11) - wires
        `Inventory.remove_item()`, which existed since the domain
        model's first implementation but was never called by anything.

        Args:
            item_id (int): id of the item to remove.
            is_food (bool): True for a FoodItem, False for a Medication.

        Raises:
            ValueError: if no matching item exists.

        Test:
            - Given a stocked FoodItem, when
              `remove_inventory_item(item_id, True)` is called, then it
              no longer appears in `get_zoo().inventory.items` nor in
              storage.
            - Given an item_id that does not exist for the requested
              kind, when `remove_inventory_item()` is called, then a
              ValueError is raised and nothing is deleted.
        """
        zoo = self.get_zoo()
        self._find_inventory_item(zoo, item_id, is_food)
        if is_food:
            self._inventory_repository.delete_item(item_id)
        else:
            self._inventory_repository.delete_medication(item_id)
        zoo.inventory.remove_item(item_id)
