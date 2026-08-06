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
-- ANIMAL and EMPLOYEE use single-table inheritance: `species` /
-- `employee_type` act as the discriminator for the concrete subclass
-- (Lion/Giraffe/Penguin, Zookeeper/Veterinarian/Administrator), since the
-- subclasses add no persisted attributes beyond what the base class already
-- has (Lion/Giraffe/Penguin only add `food_preference`).

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
    cleanliness     REAL,
    temperature     REAL
);

CREATE INDEX IF NOT EXISTS idx_enclosure_zoo_id ON enclosure (zoo_id);

CREATE TABLE IF NOT EXISTS animal (
    animal_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    enclosure_id     INTEGER REFERENCES enclosure (enclosure_id) ON DELETE SET NULL,
    name             TEXT NOT NULL,
    species          TEXT NOT NULL,
    food_preference  TEXT,
    age              INTEGER,
    health           INTEGER,
    hunger           INTEGER,
    energy           INTEGER
);

CREATE INDEX IF NOT EXISTS idx_animal_enclosure_id ON animal (enclosure_id);

CREATE TABLE IF NOT EXISTS employee (
    employee_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id         INTEGER NOT NULL REFERENCES zoo (zoo_id) ON DELETE CASCADE,
    employee_type  TEXT NOT NULL,
    name           TEXT NOT NULL,
    salary         REAL
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
    price_per_unit    REAL,
    minimum_quantity  REAL
);

CREATE INDEX IF NOT EXISTS idx_food_item_inventory_id ON food_item (inventory_id);

CREATE TABLE IF NOT EXISTS medication (
    medication_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id      INTEGER NOT NULL REFERENCES inventory (inventory_id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    quantity          REAL NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    minimum_quantity  REAL
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
