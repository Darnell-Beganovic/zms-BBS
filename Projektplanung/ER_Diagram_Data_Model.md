## ER Diagram / Data Model

Short: Entity-Relationship diagram and table definitions for the persistent data model.

```mermaid
erDiagram

ZOO ||--o{ ENCLOSURE : contains
ZOO ||--|| INVENTORY : owns
ZOO ||--o{ EMPLOYEE : employs
ZOO ||--o{ TRANSACTION : records
ZOO ||--o{ SCHEDULED_EVENT : schedules

ENCLOSURE ||--o{ ANIMAL : contains

INVENTORY ||--o{ FOOD_ITEM : stores
INVENTORY ||--o{ MEDICATION : stores

ZOO {
    int zoo_id PK
    string name
}

ENCLOSURE {
    int enclosure_id PK
    int zoo_id FK
    string name
    int capacity
}

ANIMAL {
    int animal_id PK
    int enclosure_id FK
    string species
    int age
    int health
}

EMPLOYEE {
    int employee_id PK
    int zoo_id FK
    string employee_type
}

INVENTORY {
    int inventory_id PK
    int zoo_id FK
}

FOOD_ITEM {
    int food_id PK
    int inventory_id FK
    string name
    int quantity
}

MEDICATION {
    int medication_id PK
    int inventory_id FK
    string name
    int quantity
}

TRANSACTION {
    int transaction_id PK
    int zoo_id FK
    float amount
}

SCHEDULED_EVENT {
    int event_id PK
    int zoo_id FK
    string event_type
}
```

Notes:
- `PK` marks the primary key, `FK` marks a foreign key referencing the parent entity from the relationship above (e.g. `ENCLOSURE.zoo_id` references `ZOO.zoo_id`).
- The persistence layer is SQLite only (see `Funktionale_und_nichtfunktionale_Anforderungen.md` NFR-04); no MySQL variant is planned.
- `FEEDING_RECORD` and `TREATMENT_RECORD` (not yet modeled above) could capture historical events for auditing and simulation replay if the team decides to add feeding/treatment history later.
