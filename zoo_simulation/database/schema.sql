-- schema.sql - SQLite schema for the Zoo Management System (ZMS).
--
-- Schwerpunkt: Datenbank - Kaiss Saleh
--
-- author: Kaiss Saleh
-- date: 2026-08-05
-- version: 1.0.0
-- license: Educational Use - Programming II Module
--
-- Combines the entities/relationships from
-- Projektplanung/ER_Diagram_Data_Model.md with the attribute lists from the
-- domain classes in Projektplanung/Klassendiagramm_Code.md. Foreign key
-- enforcement is enabled by SQLiteConnection.connect() (PRAGMA foreign_keys
-- = ON), so the ON DELETE rules below are actually enforced at runtime.
--
-- SCHEDULED_EVENT is intentionally NOT modeled here: per the class diagram,
-- EventScheduler keeps `scheduled_events` purely in memory (no repository
-- reads/writes it), so a table for it would never be used. It can be added
-- later if the simulation needs to persist events across runs.
--
-- BEHAVIOR is likewise intentionally NOT modeled: Behavior objects
-- (FeedingBehavior/SocialBehavior/RestBehavior) carry no state worth
-- round-tripping for this project's scope, so SQLAnimalRepository assigns
-- every reconstructed Animal a fixed default Behavior set instead (see its
-- module docstring, "Fixed 2026-08-09", and planning_db_kaiss.md section 6).
--
-- FINANCE_MANAGER is likewise NOT modeled: it is a pure in-memory wrapper
-- around the balance FinanceRepository.get_balance() already computes from
-- this schema's own `transaction` table, so persisting it separately would
-- just duplicate that number (see planning_db_kaiss.md section 6).
--
-- ANIMAL and EMPLOYEE use single-table inheritance: `species` /
-- `employee_type` act as the discriminator for the concrete subclass
-- (Lion/Giraffe/Penguin, Zookeeper/Veterinarian/Administrator), since the
-- subclasses add no persisted attributes beyond what the base class already
-- has (Lion/Giraffe/Penguin only add `food_preference`).
--
-- CHECK constraints (added 2026-08-09): every numeric column that the
-- domain model already constrains in Python (Animal._validate_value()
-- clamps health/hunger/energy to 0-100, Enclosure keeps cleanliness in
-- 0-100, Employee/FoodItem/Medication logically can't go negative) now has
-- a matching CHECK here too, so a direct/malformed INSERT (bypassing the
-- Python layer) cannot corrupt data either - defense in depth for NFR-09
-- ("Invalid operations shall not corrupt application data"), not just a
-- single point of enforcement in the domain layer.



PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS zoo (
    zoo_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,
    location           TEXT,
    current_visitors   INTEGER NOT NULL DEFAULT 0 CHECK (current_visitors >= 0),
    maximum_visitors   INTEGER NOT NULL CHECK (maximum_visitors >= 0)
);

CREATE TABLE IF NOT EXISTS enclosure (
    enclosure_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id          INTEGER NOT NULL REFERENCES zoo (zoo_id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    enclosure_type  TEXT,
    size            REAL,
    capacity        INTEGER NOT NULL CHECK (capacity >= 0),
    -- Nullable columns' CHECK is only evaluated when a value is present:
    -- SQLite treats a CHECK expression that evaluates to NULL as satisfied,
    -- so this does not force cleanliness to be set.
    cleanliness     REAL CHECK (cleanliness BETWEEN 0 AND 100),
    temperature     REAL
);

CREATE INDEX IF NOT EXISTS idx_enclosure_zoo_id ON enclosure (zoo_id);

CREATE TABLE IF NOT EXISTS animal (
    animal_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    enclosure_id     INTEGER REFERENCES enclosure (enclosure_id) ON DELETE SET NULL,
    name             TEXT NOT NULL,
    species          TEXT NOT NULL,
    food_preference  TEXT,
    age              INTEGER CHECK (age >= 0),
    health           INTEGER CHECK (health BETWEEN 0 AND 100),
    hunger           INTEGER CHECK (hunger BETWEEN 0 AND 100),
    energy           INTEGER CHECK (energy BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_animal_enclosure_id ON animal (enclosure_id);

CREATE TABLE IF NOT EXISTS employee (
    employee_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id         INTEGER NOT NULL REFERENCES zoo (zoo_id) ON DELETE CASCADE,
    employee_type  TEXT NOT NULL,
    name           TEXT NOT NULL,
    salary         REAL CHECK (salary >= 0)
);

CREATE INDEX IF NOT EXISTS idx_employee_zoo_id ON employee (zoo_id);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id        INTEGER NOT NULL UNIQUE REFERENCES zoo (zoo_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS food_item (
    food_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id      INTEGER NOT NULL REFERENCES inventory (inventory_id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    food_type         TEXT,
    quantity          REAL NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    price_per_unit    REAL CHECK (price_per_unit >= 0),
    minimum_quantity  REAL CHECK (minimum_quantity >= 0)
);

CREATE INDEX IF NOT EXISTS idx_food_item_inventory_id ON food_item (inventory_id);

CREATE TABLE IF NOT EXISTS medication (
    medication_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id      INTEGER NOT NULL REFERENCES inventory (inventory_id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    quantity          REAL NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    minimum_quantity  REAL CHECK (minimum_quantity >= 0)
);

CREATE INDEX IF NOT EXISTS idx_medication_inventory_id ON medication (inventory_id);

CREATE TABLE IF NOT EXISTS "transaction" (
    transaction_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id            INTEGER NOT NULL REFERENCES zoo (zoo_id) ON DELETE CASCADE,
    transaction_type  TEXT NOT NULL,
    amount            REAL NOT NULL,
    description       TEXT,
    created_at        TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_transaction_zoo_id ON "transaction" (zoo_id);
