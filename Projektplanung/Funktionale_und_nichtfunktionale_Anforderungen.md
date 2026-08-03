## Functional and Non-Functional Requirements

This section defines the system requirements, including priorities and acceptance criteria.

### Functional Requirements

**FR-01: Ticket Purchase**
- Visitors shall be able to purchase zoo tickets.
- **Acceptance Criteria**
  - **Given** a visitor requests a ticket
  - **When** the purchase is confirmed
  - **Then** the visitor count is updated and the transaction is recorded.

---

**FR-02: Animal Feeding**
- Zookeepers shall be able to feed animals and document the feeding process.
- **Acceptance Criteria**
  - **Given** a selected animal and available food
  - **When** the zookeeper performs a feeding
  - **Then** the animal's hunger level decreases and the food inventory is updated.

---

**FR-03: Enclosure Management**
- The system shall manage enclosure conditions, including cleanliness and temperature.
- **Acceptance Criteria**
  - **Given** an enclosure exists
  - **When** its status is updated
  - **Then** the new enclosure data is stored successfully.

---

**FR-04: Veterinary Care**
- Veterinarians shall be able to examine and treat animals.
- **Acceptance Criteria**
  - **Given** an animal requires medical attention
  - **When** the veterinarian performs a treatment
  - **Then** the animal's health status and medication usage are updated.

---

**FR-05: Financial Reporting**
- Administrators shall be able to generate financial reports in CSV and Excel format.
- **Acceptance Criteria**
  - **Given** financial data exists
  - **When** the administrator generates a report
  - **Then** the report is exported successfully.

---

**FR-06: Simulation Execution**
- The SimulationEngine shall execute simulation steps and update animals, enclosures, and environmental conditions.
- **Acceptance Criteria**
  - **Given** the simulation is running
  - **When** a simulation step is executed
  - **Then** all affected objects are updated correctly.

---

### Non-Functional Requirements

**NFR-01: Performance**
- User interactions should have a response time below **500 ms** under normal operating conditions.

**NFR-02: Maintainability**
- The software shall follow object-oriented design principles and a layered architecture to simplify future extensions.

**NFR-03: Reliability**
- Application data shall be stored persistently using SQLite via the Repository Pattern.

**NFR-04: Extensibility**
- The system shall support the addition of new animal species, employee types, and simulation behaviors without requiring modifications to existing core classes.

Note: user authentication and role-based authorization are explicitly out of
scope for this project (see `planning.md` section 4.2); there is no NFR for
security/authentication.

---

### Priority

**High**
- FR-01
- FR-02
- FR-06

**Medium**
- FR-03
- FR-04
- FR-05
- NFR-01

**Low**
- NFR-02
- NFR-03
- NFR-04

---

### Traceability

| Requirement | Related Classes |
|-------------|-----------------|
| FR-01 | `ZooService`, `FinanceManager`, `Transaction` |
| FR-02 | `Zookeeper`, `Animal`, `FoodItem`, `Inventory` |
| FR-03 | `Enclosure` |
| FR-04 | `Veterinarian`, `Medication` |
| FR-05 | `ReportService`, `FinanceRepository` |
| FR-06 | `SimulationEngine`, `EventScheduler`, `EnvironmentalFactor` |

---

### Acceptance Criteria and Validation

- Every functional requirement includes at least one Given/When/Then scenario.
- As required by the module assignment, test cases for each requirement are described (see the Test Plan in `planning.md`) but are not implemented as automated tests.
- Non-functional requirements shall be verified through code reviews and architectural evaluation.
