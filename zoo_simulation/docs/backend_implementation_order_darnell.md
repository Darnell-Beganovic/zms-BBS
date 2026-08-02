# Backend Implementation Order (Darnell Beganovic)

Chronologische Reihenfolge zur Implementierung der Backend-Klassen, sortiert
nach Abhaengigkeiten (Basisklassen/Blaetter zuerst, danach alles was darauf
aufbaut). ReportService gehoert nicht mehr zum Backend-Scope, siehe
[`planning_backend_darnell.md`](planning_backend_darnell.md) und
[`planning_db_kaiss.md`](planning_db_kaiss.md) (Umverteilung an Kaiss,
Datenbank-Schwerpunkt).

## 1. Reine Datenklassen (keine Abhaengigkeiten)

1. `domain/transaction.py` - `Transaction`: `is_valid()`
2. `domain/food_item.py` - `FoodItem`: `increase_quantity()`, `decrease_quantity()`, `is_low_stock()`
3. `domain/medication.py` - `Medication`: `increase_quantity()`, `decrease_quantity()`, `is_low_stock()`
4. `simulation/environmental_factor.py` - `EnvironmentalFactor`: `get_influence_factor()`

## 2. Abstrakte Basisklassen

5. `domain/animals/animal.py` - `Animal`: `update()`, `calculate_welfare()`, `#validate_value()`, abstrakte `eat()`, `sleep()`, `move()`, `grow_older()`
6. `domain/employees/employee.py` - `Employee`: `calculate_daily_salary()`, abstrakte `perform_task()`

## 3. Konkrete Tierarten (erben von Animal)

7. `domain/animals/lion.py` - `Lion`: `eat()`, `sleep()`, `move()`, `grow_older()`
8. `domain/animals/giraffe.py` - `Giraffe`: `eat()`, `sleep()`, `move()`, `grow_older()`
9. `domain/animals/penguin.py` - `Penguin`: `eat()`, `sleep()`, `move()`, `grow_older()`

## 4. Ressourcen- und Verwaltungsklassen, die die obigen nutzen

10. `domain/inventory.py` - `Inventory`: `add_item()`, `remove_item()`, `consume_item()`, `get_low_stock_items()`
11. `domain/finance_manager.py` - `FinanceManager`: `record_income()`, `record_expense()`, `get_balance()`
12. `domain/enclosure.py` - `Enclosure`: `add_animal()`, `remove_animal()`, `has_capacity()`, `clean()`, `update()`

## 5. Konkrete Mitarbeitertypen (erben von Employee, nutzen Enclosure/Animal/Inventory)

13. `domain/employees/zookeeper.py` - `Zookeeper`: `perform_task()`, `feed_animal()`, `clean_enclosure()`
14. `domain/employees/veterinarian.py` - `Veterinarian`: `perform_task()`, `examine_animal()`, `treat_animal()`
15. `domain/employees/administrator.py` - `Administrator`: `perform_task()`, `record_income()`, `record_expense()`

## 6. Zentrale Aggregatklasse

16. `domain/zoo.py` - `Zoo`: `add_enclosure()`, `add_employee()`, `register_visitor()`, `calculate_average_welfare()`

## 7. Simulationskern (nutzt Zoo, Animal, EnvironmentalFactor)

17. `simulation/event_scheduler.py` - `EventScheduler`: `schedule_event()`, `get_due_events()`, `execute_due_events()`
18. `simulation/simulation_engine.py` - `SimulationEngine`: `tick()`, `update_animals()`, `update_enclosures()`, `process_daily_costs()`

## 8. Service-Layer (nutzt Domain + Repository-Interfaces von Kaiss)

19. `services/zoo_service.py` - `ZooService`: `get_zoo()`, `add_animal()`, `feed_animal()`, `hire_employee()`, `sell_ticket()`
20. `services/simulation_service.py` - `SimulationService`: `run_step()`, `run_steps()`, `get_simulation_time()`

## 9. Controller (nutzt alle Services)

21. `controller/zoo_controller.py` - `ZooController`: `show_status()`, `add_animal()`, `feed_animal()`, `run_simulation_step()`, `create_report()`
