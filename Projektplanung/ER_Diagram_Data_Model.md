## ER Diagram / Data Model

Short: Entity-Relationship diagram and table definitions for the persistent data model.

```mermaid
erDiagram

ZOO ||--o{ ENCLOSURE : contains
ZOO ||--|| INVENTORY : owns
ZOO ||--o{ EMPLOYEE : employs
ZOO ||--o{ TRANSACTION : records

ENCLOSURE |o--o{ ANIMAL : contains

INVENTORY ||--o{ FOOD_ITEM : stores
INVENTORY ||--o{ MEDICATION : stores

ZOO {
    int zoo_id PK
    string name
    string location
    int current_visitors
    int maximum_visitors
}

ENCLOSURE {
    int enclosure_id PK
    int zoo_id FK
    string name
    string enclosure_type
    float size
    int capacity
    float cleanliness
    float temperature
}

ANIMAL {
    int animal_id PK
    int enclosure_id FK
    string name
    string species
    string food_preference
    int age
    int health
    int hunger
    int energy
}

EMPLOYEE {
    int employee_id PK
    int zoo_id FK
    string employee_type
    string name
    float salary
}

INVENTORY {
    int inventory_id PK
    int zoo_id FK
}

FOOD_ITEM {
    int food_id PK
    int inventory_id FK
    string name
    string food_type
    float quantity
    float price_per_unit
    float minimum_quantity
}

MEDICATION {
    int medication_id PK
    int inventory_id FK
    string name
    float quantity
    float minimum_quantity
}

TRANSACTION {
    int transaction_id PK
    int zoo_id FK
    string transaction_type
    float amount
    string description
    string created_at
}
```

Notes:
- `PK` marks the primary key, `FK` marks a foreign key referencing the parent entity from the relationship above (e.g. `ENCLOSURE.zoo_id` references `ZOO.zoo_id`).
- `ENCLOSURE |o--o{ ANIMAL` is intentionally zero-or-one on the `ENCLOSURE` side: `ANIMAL.enclosure_id` is a nullable FK, so an animal can exist without being assigned to an enclosure (e.g. right after creation, or while being moved). This matches the Aggregation semantics in `planning.md` §8.5 ("Animals can be moved between different Enclosures", i.e. `Animal` exists independently of `Enclosure`).
- The persistence layer is SQLite only (see `Funktionale_und_nichtfunktionale_Anforderungen.md` NFR-03); no MySQL variant is planned.
- `SCHEDULED_EVENT` is intentionally **not** modeled as a table: per the class diagram, `EventScheduler` keeps `scheduled_events` purely in memory (no repository reads/writes it), so a persisted table would never be used. It can be added later if the simulation needs to persist events across runs.
- `FEEDING_RECORD` and `TREATMENT_RECORD` (not yet modeled above) could capture historical events for auditing and simulation replay if the team decides to add feeding/treatment history later.
