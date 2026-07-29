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
    int zoo_id
    string name
}

ENCLOSURE {
    int enclosure_id
    string name
    int capacity
}

ANIMAL {
    int animal_id
    string species
    int age
    int health
}

EMPLOYEE {
    int employee_id
    string employee_type
}

INVENTORY {
    int inventory_id
}

FOOD_ITEM {
    int food_id
    string name
    int quantity
}

MEDICATION {
    int medication_id
    string name
    int quantity
}

TRANSACTION {
    int transaction_id
    float amount
}

SCHEDULED_EVENT {
    int event_id
    string event_type
}
```

Notes:
- Use `FK` to indicate foreign keys; adapt types for chosen DB (SQLite vs MySQL).
- `SPECIES` is separated to allow easy addition of new species without schema changes to `ANIMAL`.
- `FEEDING_RECORD` and `TREATMENT_RECORD` capture historical events for auditing and simulation replay.

Next: review the ER model and tell me `next` to produce SQL table skeletons or move to `Klassendiagramme vervollständigen`.
