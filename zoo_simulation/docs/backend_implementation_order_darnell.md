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

## 2. Verhalten-Hierarchie (Komposition mit Animal, siehe aufgabe.md Teilbereich 2)

`Animal` wird mit 1..* `Behavior`-Objekten komponiert (`Animal *-- "1..*" Behavior`,
volles Diagramm in `../../Projektplanung/Klassendiagramm_Code.md`). Das ist
funktional, nicht nur strukturell: `Animal.update()` iteriert ueber seine
Behaviors und ruft `execute(self)` auf; jedes Behavior wirkt isoliert auf
genau einen Stat (kein Blending mehrerer Behaviors zu einem komplexen
Muster - bewusst einfach gehalten, siehe Ruecksprache mit Darnell
2026-08-06).

5. `domain/behaviors/behavior.py` - `Behavior` (abstrakt): abstrakte `execute(animal: Animal)`
6. `domain/behaviors/feeding_behavior.py` - `FeedingBehavior`: `execute()` (wirkt auf `hunger`)
7. `domain/behaviors/social_behavior.py` - `SocialBehavior`: `execute()` (wirkt auf `energy`)
8. `domain/behaviors/rest_behavior.py` - `RestBehavior`: `execute()` (wirkt auf `energy`/`health`)

## 3. Abstrakte Basisklassen

9. `domain/animals/animal.py` - `Animal`: `update()`, `calculate_welfare()`, `#validate_value()`, abstrakte `eat()`, `sleep()`, `move()`, `grow_older()`
10. `domain/employees/employee.py` - `Employee`: `calculate_daily_salary()`, abstrakte `perform_task()`

## 4. Konkrete Tierarten (erben von Animal)

11. `domain/animals/lion.py` - `Lion`: `-food_preference`, `eat()`, `sleep()`, `move()`, `grow_older()`, `typical_behavior()`
12. `domain/animals/giraffe.py` - `Giraffe`: `-food_preference`, `eat()`, `sleep()`, `move()`, `grow_older()`, `typical_behavior()`
13. `domain/animals/penguin.py` - `Penguin`: `-food_preference`, `eat()`, `sleep()`, `move()`, `grow_older()`, `typical_behavior()`

## 5. Ressourcen- und Verwaltungsklassen, die die obigen nutzen

14. `domain/inventory.py` - `Inventory`: `add_item()`, `remove_item()`, `consume_item()`, `get_low_stock_items()`
15. `domain/finance_manager.py` - `FinanceManager`: `record_income()`, `record_expense()`, `get_balance()`
16. `domain/enclosure.py` - `Enclosure`: `add_animal()`, `remove_animal()`, `has_capacity()`, `clean()`, `update()`

## 6. Konkrete Mitarbeitertypen (erben von Employee, nutzen Enclosure/Animal/Inventory)

17. `domain/employees/zookeeper.py` - `Zookeeper`: `perform_task()`, `feed_animal()`, `clean_enclosure()`
18. `domain/employees/veterinarian.py` - `Veterinarian`: `perform_task()`, `examine_animal()`, `treat_animal()`
19. `domain/employees/administrator.py` - `Administrator`: `perform_task()`, `record_income()`, `record_expense()`

## 7. Zentrale Aggregatklasse

20. `domain/zoo.py` - `Zoo`: `add_enclosure()`, `add_employee()`, `register_visitor()`, `calculate_average_welfare()`

## 8. Simulationskern (nutzt Zoo, Animal, EnvironmentalFactor)

21. `simulation/event_scheduler.py` - `EventScheduler`: `schedule_event()`, `get_due_events()`, `execute_due_events()`
22. `simulation/simulation_engine.py` - `SimulationEngine`: `tick()`, `update_animals()`, `update_enclosures()`, `process_daily_costs()`

## 9. Service-Layer (nutzt Domain + Repository-Interfaces von Kaiss)

23. `services/zoo_service.py` - `ZooService`: `get_zoo()`, `add_animal()`, `feed_animal()`, `hire_employee()`, `sell_ticket()`
24. `services/simulation_service.py` - `SimulationService`: `run_step()`, `run_steps()`, `get_simulation_time()`

## 10. Controller (nutzt alle Services)

25. `controller/zoo_controller.py` - `ZooController`: `show_status()`, `add_animal()`, `feed_animal()`, `run_simulation_step()`, `create_report()`
