---
title: Zoo-Simulation – Klassendiagramm (überarbeitet)
---

```mermaid
classDiagram
    direction TB
    %% =========================
    %% MVC: VIEW AND CONTROLLER
    %% =========================

    class ZooView {
        <<Flask blueprint>>
        +show_zoo_status(data: DataFrame) void
        +show_animals(data: DataFrame) void
        +show_financial_report(data: DataFrame) void
        +show_message(message: str) void
    }

    %% NOTE (2026-08-06, agreed Frontend/Backend): ZooController methods
    %% return a uniform result dict {"success": bool, "message": str,
    %% "data": Any} instead of void, so ZooView can render success/error
    %% messages and the returned data without touching the service layer.
    %% sell_ticket() was added to close a gap between the frontend route
    %% table (/tickets/buy) and this diagram, which had no ticket method.
    class ZooController {
        -ZooService zoo_service
        -SimulationService simulation_service
        -ReportService report_service
        +show_status() dict
        +add_animal(data: dict) dict
        +feed_animal(animal_id: int, food_id: int) dict
        +hire_employee(data: dict) dict
        +clean_enclosure(enclosure_id: int) dict
        +sell_ticket(price: float) dict
        +run_simulation_step() dict
        +create_report(format: str) dict
    }

    %% =========================
    %% SERVICE LAYER
    %% =========================

    class ZooService {
        -int zoo_id
        -ZooRepository zoo_repository
        -AnimalRepository animal_repository
        -EnclosureRepository enclosure_repository
        -EmployeeRepository employee_repository
        -InventoryRepository inventory_repository
        -FinanceRepository finance_repository
        +get_zoo() Zoo
        +add_animal(animal: Animal, enclosure_id: int) int
        +feed_animal(animal_id: int, food_id: int) void
        +hire_employee(employee: Employee) void
        +clean_enclosure(enclosure_id: int) void
        +sell_ticket(price: float) void
    }

    class SimulationService {
        -SimulationEngine simulation_engine
        +run_step() void
        +run_steps(number_of_steps: int) void
        +get_simulation_time() int
    }

    class ReportService {
        -AnimalRepository animal_repository
        -FinanceRepository finance_repository
        -InventoryRepository inventory_repository
        +create_animal_report() DataFrame
        +create_financial_report() DataFrame
        +create_inventory_report() DataFrame
        +export_csv(data: DataFrame, file_path: str) void
        +export_excel(data: DataFrame, file_path: str) void
    }

    %% =========================
    %% DOMAIN MODEL - ZOO VERWALTUNG
    %% =========================

    class Zoo {
        -int id
        -str name
        -str location
        -int current_visitors
        -int maximum_visitors
        +add_enclosure(enclosure: Enclosure) void
        +add_employee(employee: Employee) void
        +register_visitor() bool
        +calculate_average_welfare() float
    }

    class Enclosure {
        -int id
        -str name
        -str enclosure_type
        -float size
        -int capacity
        -float cleanliness
        -float temperature
        +add_animal(animal: Animal) void
        +remove_animal(animal_id: int) void
        +has_capacity() bool
        +clean() void
        +update(temperature: Optional[float]) void
    }

    class Employee {
        <<abstract>>
        -int id
        -str name
        -float salary
        +perform_task() str*
        +calculate_daily_salary() float
    }

    class Zookeeper {
        +perform_task() str
        +feed_animal(animal: Animal, food: FoodItem) void
        +clean_enclosure(enclosure: Enclosure) void
    }

    class Veterinarian {
        +perform_task() str
        +examine_animal(animal: Animal) str
        +treat_animal(animal: Animal, medication: Medication) void
    }

    class Administrator {
        -FinanceManager finance_manager
        +perform_task() str
        +record_income(amount: float) void
        +record_expense(amount: float) void
    }

    class Inventory {
        -int id
        +add_item(item: FoodItem|Medication) void
        +remove_item(item_id: int) void
        +consume_item(item_id: int, quantity: float) bool
        +get_low_stock_items() list
    }

    class FoodItem {
        -int id
        -str name
        -str food_type
        -float quantity
        -float price_per_unit
        -float minimum_quantity
        +increase_quantity(amount: float) void
        +decrease_quantity(amount: float) bool
        +is_low_stock() bool
    }

    class Medication {
        -int id
        -str name
        -float quantity
        -float minimum_quantity
        +increase_quantity(amount: float) void
        +decrease_quantity(amount: float) bool
        +is_low_stock() bool
    }

    class FinanceManager {
        -float balance
        +record_income(amount: float, description: str) Transaction
        +record_expense(amount: float, description: str) Transaction
        +get_balance() float
    }

    class Transaction {
        -int id
        -str transaction_type
        -float amount
        -str description
        -datetime created_at
        +is_valid() bool
    }

    %% =========================
    %% DOMAIN MODEL - TIERSIMULATION
    %% =========================

    class Animal {
        <<abstract>>
        -int id
        -str name
        -str species
        -int age
        -int health
        -int hunger
        -int energy
        +eat(food: FoodItem) void*
        +sleep() void*
        +move() str*
        +grow_older() void*
        +update() void
        +calculate_welfare() float
        +adjust_health(delta: int) void
        +adjust_hunger(delta: int) void
        +adjust_energy(delta: int) void
        #validate_value(value: int) int
    }

    class Lion {
        -str food_preference
        +eat(food: FoodItem) void
        +sleep() void
        +move() str
        +grow_older() void
        +typical_behavior() str
    }

    class Giraffe {
        -str food_preference
        +eat(food: FoodItem) void
        +sleep() void
        +move() str
        +grow_older() void
        +typical_behavior() str
    }

    class Penguin {
        -str food_preference
        +eat(food: FoodItem) void
        +sleep() void
        +move() str
        +grow_older() void
        +typical_behavior() str
    }

    class Behavior {
        <<abstract>>
        +execute(animal: Animal) void*
    }

    class FeedingBehavior {
        -str food_preference
        +execute(animal: Animal) void
    }

    class SocialBehavior {
        -int social_level
        +execute(animal: Animal) void
    }

    class RestBehavior {
        -int rest_duration
        +execute(animal: Animal) void
    }

    class EnvironmentalFactor {
        -float temperature
        -str time_of_day
        -str weather_condition
        +get_influence_factor() float
    }

    %% =========================
    %% SIMULATIONSKERN
    %% =========================

    class SimulationEngine {
        -Zoo zoo
        -EventScheduler event_scheduler
        -EnvironmentalFactor environment
        -int current_step
        +tick() void
        +update_animals() void
        +update_enclosures() void
        +process_daily_costs() void
    }

    class EventScheduler {
        -list scheduled_events
        +schedule_event(event: dict, trigger_time: int) void
        +get_due_events(current_time: int) list
        +execute_due_events(current_time: int) void
    }

    %% =========================
    %% REPOSITORY INTERFACES
    %% =========================

    class ZooRepository {
        <<interface>>
        +save(zoo: Zoo) int
        +get_by_id(zoo_id: int) Zoo
        +update(zoo: Zoo) void
    }

    %% enclosure_id is passed separately from the Animal object because
    %% Animal itself carries no enclosure_id attribute (unidirectional
    %% aggregation Enclosure o-- Animal); this mirrors
    %% ZooService.add_animal(animal, enclosure_id) below.
    %% update()'s enclosure_id is Optional: None means "leave the current
    %% enclosure assignment unchanged", not "unassign".
    class AnimalRepository {
        <<interface>>
        +save(animal: Animal, enclosure_id: int) int
        +get_by_id(animal_id: int) Animal
        +get_all() list
        +update(animal: Animal, enclosure_id: Optional[int]) void
        +delete(animal_id: int) void
        +get_as_dataframe() DataFrame
    }

    class EnclosureRepository {
        <<interface>>
        +save(enclosure: Enclosure, zoo_id: int) int
        +get_by_id(enclosure_id: int) Enclosure
        +get_all() list
        +update(enclosure: Enclosure) void
    }

    class EmployeeRepository {
        <<interface>>
        +save(employee: Employee, zoo_id: int) int
        +get_by_id(employee_id: int) Employee
        +get_all() list
        +update(employee: Employee) void
        +delete(employee_id: int) void
    }

    %% get_inventory() added 2026-08-09: reconstructs the full Inventory
    %% aggregate (not just individual items) - needed so ZooRepository can
    %% build a complete Zoo (Zoo *-- "1" Inventory), see
    %% planning_db_kaiss.md section 2.1/6.
    class InventoryRepository {
        <<interface>>
        +save_item(item: FoodItem, inventory_id: int) int
        +get_item(item_id: int) FoodItem
        +get_all_items() list
        +update_item(item: FoodItem) void
        +save_medication(medication: Medication, inventory_id: int) int
        +get_medication(medication_id: int) Medication
        +get_all_medications() list
        +update_medication(medication: Medication) void
        +get_as_dataframe() DataFrame
        +get_inventory(zoo_id: int) Inventory
        +create_inventory(zoo_id: int) int
    }

    class FinanceRepository {
        <<interface>>
        +save_transaction(transaction: Transaction, zoo_id: int) int
        +get_all_transactions() list
        +get_balance() float
        +get_as_dataframe() DataFrame
    }

    %% =========================
    %% DATABASE LAYER
    %% =========================

    class DatabaseConnection {
        <<interface>>
        +connect() void
        +execute(query: str, parameters: tuple) object
        +commit() void
        +rollback() void
        +close() void
    }

    class SQLiteConnection {
        -str database_path
        +connect() void
        +execute(query: str, parameters: tuple) object
        +commit() void
        +rollback() void
        +close() void
        #require_connection() Connection
    }

    %% SQLZooRepository composes the three sibling repositories below
    %% (added 2026-08-09) so row_to_zoo() can build a *complete* Zoo -
    %% Enclosures/Inventory/FinanceManager are all required constructor
    %% arguments (Zoo *-- Enclosure/Inventory/FinanceManager) but none are
    %% columns on the zoo table itself. See planning_db_kaiss.md section
    %% 2.1/6 for the full rationale, including the single-zoo scoping
    %% assumption this relies on.
    class SQLZooRepository {
        -DatabaseConnection connection
        -EnclosureRepository enclosure_repository
        -InventoryRepository inventory_repository
        -FinanceRepository finance_repository
        -EmployeeRepository employee_repository
        +save(zoo: Zoo) int
        +get_by_id(zoo_id: int) Zoo
        +update(zoo: Zoo) void
        #row_to_zoo(row: Row) Zoo
    }

    %% default_behaviors() added 2026-08-09: Behavior is not persisted (no
    %% table, see database/schema.sql's header comment), so
    %% row_to_animal() assigns every reconstructed Animal a fixed default
    %% Behavior set instead of leaving the required Animal(behaviors=...)
    %% argument unfilled. See planning_db_kaiss.md section 2.1/6.
    class SQLAnimalRepository {
        -DatabaseConnection connection
        +save(animal: Animal, enclosure_id: int) int
        +get_by_id(animal_id: int) Animal
        +get_all() list
        +update(animal: Animal, enclosure_id: Optional[int]) void
        +delete(animal_id: int) void
        +get_as_dataframe() DataFrame
        #row_to_animal(row: Row) Animal
        #default_behaviors(food_preference: str) list
    }

    class SQLEnclosureRepository {
        -DatabaseConnection connection
        +save(enclosure: Enclosure, zoo_id: int) int
        +get_by_id(enclosure_id: int) Enclosure
        +get_all() list
        +update(enclosure: Enclosure) void
        #row_to_enclosure(row: Row) Enclosure
    }

    %% finance_repository added 2026-08-09: Administrator requires a
    %% FinanceManager (constructor-injected, see planning_backend_darnell.md
    %% section 2.3) that no column on the employee table can supply -
    %% row_to_employee() builds one from FinanceRepository.get_balance()
    %% for Administrator rows only. See planning_db_kaiss.md section 2.1/6.
    class SQLEmployeeRepository {
        -DatabaseConnection connection
        -FinanceRepository finance_repository
        +save(employee: Employee, zoo_id: int) int
        +get_by_id(employee_id: int) Employee
        +get_all() list
        +update(employee: Employee) void
        +delete(employee_id: int) void
        #row_to_employee(row: Row) Employee
    }

    class SQLInventoryRepository {
        -DatabaseConnection connection
        +save_item(item: FoodItem, inventory_id: int) int
        +get_item(item_id: int) FoodItem
        +get_all_items() list
        +update_item(item: FoodItem) void
        +save_medication(medication: Medication, inventory_id: int) int
        +get_medication(medication_id: int) Medication
        +get_all_medications() list
        +update_medication(medication: Medication) void
        +get_as_dataframe() DataFrame
        +get_inventory(zoo_id: int) Inventory
        +create_inventory(zoo_id: int) int
    }

    class SQLFinanceRepository {
        -DatabaseConnection connection
        +save_transaction(transaction: Transaction, zoo_id: int) int
        +get_all_transactions() list
        +get_balance() float
        +get_as_dataframe() DataFrame
        #row_to_transaction(row: Row) Transaction
    }

    %% =========================
    %% INHERITANCE
    %% =========================

    Animal <|-- Lion
    Animal <|-- Giraffe
    Animal <|-- Penguin

    Employee <|-- Zookeeper
    Employee <|-- Veterinarian
    Employee <|-- Administrator

    Behavior <|-- FeedingBehavior
    Behavior <|-- SocialBehavior
    Behavior <|-- RestBehavior

    DatabaseConnection <|.. SQLiteConnection

    ZooRepository <|.. SQLZooRepository
    AnimalRepository <|.. SQLAnimalRepository
    EnclosureRepository <|.. SQLEnclosureRepository
    EmployeeRepository <|.. SQLEmployeeRepository
    InventoryRepository <|.. SQLInventoryRepository
    FinanceRepository <|.. SQLFinanceRepository

    %% =========================
    %% DOMAIN RELATIONSHIPS
    %% =========================

    Zoo *-- "1..*" Enclosure : owns
    Zoo o-- "0..*" Employee : employs
    Zoo *-- "1" Inventory : owns
    Zoo *-- "1" FinanceManager : owns

    Enclosure o-- "0..*" Animal : houses
    Inventory *-- "0..*" FoodItem : contains
    Inventory *-- "0..*" Medication : contains
    FinanceManager *-- "0..*" Transaction : creates

    Animal *-- "1..*" Behavior : composed of

    Zookeeper ..> Animal : feeds
    Zookeeper ..> Enclosure : cleans
    Zookeeper ..> FoodItem : uses
    Veterinarian ..> Animal : treats
    Veterinarian ..> Medication : uses
    Administrator --> FinanceManager : manages

    EnvironmentalFactor ..> Behavior : influences

    SimulationEngine --> Zoo : updates
    SimulationEngine --> EventScheduler : uses
    SimulationEngine --> EnvironmentalFactor : uses
    SimulationEngine ..> Animal : simulates
    SimulationEngine ..> Enclosure : simulates

    %% =========================
    %% MVC AND SERVICE RELATIONSHIPS
    %% =========================

    ZooView --> ZooController : user actions
    ZooController --> ZooService
    ZooController --> SimulationService
    ZooController --> ReportService

    ZooService --> ZooRepository
    ZooService --> AnimalRepository
    ZooService --> EnclosureRepository
    ZooService --> EmployeeRepository
    ZooService --> InventoryRepository
    ZooService --> FinanceRepository

    SimulationService --> SimulationEngine

    ReportService --> AnimalRepository
    ReportService --> InventoryRepository
    ReportService --> FinanceRepository

    %% =========================
    %% DATABASE RELATIONSHIPS
    %% =========================

    SQLZooRepository --> DatabaseConnection
    SQLAnimalRepository --> DatabaseConnection
    SQLEnclosureRepository --> DatabaseConnection
    SQLEmployeeRepository --> DatabaseConnection
    SQLInventoryRepository --> DatabaseConnection
    SQLFinanceRepository --> DatabaseConnection

    %% Added 2026-08-09 (see planning_db_kaiss.md section 2.1/6):
    %% SQLZooRepository composes its sibling repositories to reconstruct a
    %% full Zoo aggregate; SQLEmployeeRepository needs FinanceRepository
    %% to build an Administrator's FinanceManager.
    SQLZooRepository --> EnclosureRepository : loads Enclosures
    SQLZooRepository --> InventoryRepository : loads Inventory
    SQLZooRepository --> FinanceRepository : loads balance
    SQLZooRepository --> EmployeeRepository : loads Employees
    SQLEmployeeRepository --> FinanceRepository : builds Administrator's FinanceManager
```