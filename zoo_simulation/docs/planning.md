# Software Design and Project Planning

## 1. Project Overview

The Zoo Management System (ZMS) is a Python-based software project developed
as part of the Programming II module.

The objective of the project is to design and implement a digital twin of a zoo
using object-oriented programming principles. The application represents both
administrative and biological processes within a zoo.

The system includes the management of animals, enclosures, employees,
inventory and finances. In addition, a discrete time-based simulation changes
animal states, enclosure conditions and scheduled events over time.

The application follows a modular layered architecture. The user interface,
application logic, domain model, simulation logic and database access are
separated into independent components with clearly defined responsibilities.

SQLite is planned for persistent data storage. Financial and operational data
can later be exported as CSV and Excel reports.

The project is developed collaboratively by Kaiss Saleh, Alessio Bellamacina
and Darnell Beganovic. The main responsibilities are divided between the team
members, while architecture, integration, review and documentation remain
shared tasks. Each member additionally keeps an individual planning document
for their own focus area, as required by the module assignment:

- [`planning_backend_darnell.md`](planning_backend_darnell.md) — Darnell Beganovic (Backend)
- [`planning_frontend_alessio.md`](planning_frontend_alessio.md) — Alessio Bellamacina (Frontend)
- [`planning_db_kaiss.md`](planning_db_kaiss.md) — Kaiss Saleh (Database)

This document (`planning.md`) covers the parts that are shared across the
whole team: overall scope, architecture, domain model and simulation design.
The detailed Mermaid diagrams referenced throughout this document live in the
[`Projektplanung/`](../../Projektplanung) folder at the repository root.

## 2. Team Members and Responsibilities

The Zoo Management System is developed collaboratively by three team members.
To ensure a balanced workload and a clear distribution of responsibilities,
each member is primarily responsible for a specific part of the project.

### Alessio Bellamacina — Frontend

Primary responsibilities:

- Design and implementation of the Flask-based web user interface
- Routes, templates and view logic (presentation layer)
- Presenting zoo status, animal data and financial reports to the user
- Input forms and client-facing input validation
- Review of object-oriented design principles

See [`planning_frontend_alessio.md`](planning_frontend_alessio.md) for the detailed individual planning.

### Kaiss Saleh — Database

Primary responsibilities:

- Database design
- SQLite implementation
- Repository pattern
- Data persistence
- Inventory and finance repositories
- CSV and Excel report generation (`ReportService`)

See [`planning_db_kaiss.md`](planning_db_kaiss.md) for the detailed individual planning.

### Darnell Beganovic — Backend

Primary responsibilities:

- Domain model (`Zoo`, `Employee`, `Animal` hierarchies, `Enclosure`, `Inventory`, `FinanceManager`)
- Service layer and controller layer
- Simulation logic and the `SimulationEngine`
- Application workflow and server-side input validation
- Test case documentation

See [`planning_backend_darnell.md`](planning_backend_darnell.md) for the detailed individual planning.

### Shared Responsibilities

The following tasks are performed collaboratively by all team members:

- Project planning
- Software architecture
- UML diagrams
- Integration of all components
- Code reviews
- Documentation
- Git version control
- Final verification and project submission

Although each member has primary responsibilities, all major design decisions
are discussed and reviewed together to ensure a consistent software architecture.

## 3. Project Goals

The main goal of this project is to design and implement a modular Zoo
Management System that applies the principles of object-oriented programming in
a realistic software engineering project.

The system should model both the administrative and biological aspects of a zoo
while providing a clear, maintainable and extensible software architecture.

### Functional Goals

The project aims to:

- manage animals, enclosures and employees
- manage inventory and financial transactions
- simulate animal behaviour over time
- support scheduled events within the simulation
- store application data persistently using SQLite
- generate CSV and Excel reports

### Technical Goals

The project aims to:

- apply object-oriented programming principles
- design a layered software architecture
- separate presentation, business logic and persistence
- use the Repository Pattern for database access
- create reusable and maintainable software components
- document the complete software design before implementation

### Learning Goals

Through this project, the team aims to improve practical skills in:

- object-oriented software development
- software architecture and design
- database integration
- collaborative software development using Git
- software documentation
- applying design patterns in real-world applications

## 4. Project Scope

The project scope defines the functionality that is planned for implementation
and clearly distinguishes it from features that are intentionally excluded.

### 4.1 In Scope

The following features are included in the project:

- Management of animals
- Management of enclosures
- Management of employees
- Inventory management for food and medication
- Financial management
- Time-based zoo simulation
- Animal behaviour simulation (feeding, sleeping, moving and aging)
- Environmental influences on animals
- Event scheduling
- SQLite database persistence
- CSV and Excel report generation
- Flask-based web user interface
- Layered software architecture
- Repository Pattern
- Object-oriented software design

### 4.2 Out of Scope

The following features are intentionally excluded from the project:

- Graphical desktop application (native GUI toolkit)
- User authentication and authorization
- Multi-user support
- REST API
- Cloud deployment
- Mobile application
- Online payment systems
- Email notifications
- Artificial intelligence for animal behaviour
- Network communication
- Distributed databases
- Real-time synchronization

## 5. Functional Requirements

The following functional requirements define the expected functionality of the
Zoo Management System.

| ID | Requirement |
|----|-------------|
| FR-01 | The system shall manage animals, including creating, updating and removing animal records. |
| FR-02 | The system shall manage enclosures and assign animals to suitable enclosures. |
| FR-03 | The system shall manage different employee roles within the zoo. |
| FR-04 | The system shall manage food, medication and other inventory items. |
| FR-05 | The system shall feed animals and update their state accordingly. |
| FR-06 | The system shall allow veterinarians to examine and treat animals. |
| FR-07 | The system shall simulate animal behaviour using discrete simulation steps. |
| FR-08 | The system shall process scheduled events during the simulation. |
| FR-09 | The system shall manage financial transactions such as ticket sales and operating expenses. |
| FR-10 | The system shall store and retrieve data using an SQLite database. |
| FR-11 | The system shall generate reports in CSV and Excel format. |
| FR-12 | The system shall validate all user input before processing operations. |
| FR-13 | The system shall display informative success and error messages to the user. |
| FR-14 | The system shall save changes to persistent storage after successful operations. |
| FR-15 | The system shall provide a Flask-based web user interface for interacting with the application. |

## 6. Non-Functional Requirements

The following non-functional requirements define the quality attributes of the
Zoo Management System.

| ID | Requirement |
|----|-------------|
| NFR-01 | The application shall be implemented in Python 3.14. |
| NFR-02 | The application shall follow object-oriented programming principles. |
| NFR-03 | The application shall use a modular layered architecture. |
| NFR-04 | The presentation layer, business logic and persistence layer shall be clearly separated. |
| NFR-05 | The application shall use SQLite as its persistence layer. |
| NFR-06 | The source code shall be maintainable, readable and well documented. |
| NFR-07 | The application shall be extensible with additional animal species, employee roles and simulation features. |
| NFR-08 | The Repository Pattern shall allow replacing the database implementation with minimal changes. |
| NFR-09 | Invalid operations shall not corrupt application data. |
| NFR-10 | All user input shall be validated before processing. |
| NFR-11 | The application shall provide meaningful error messages for invalid operations. |
| NFR-12 | The software shall be developed using Git for version control. |
| NFR-13 | The software design shall be fully documented before implementation begins. |

## 7. System Architecture

The Zoo Management System follows a layered software architecture to achieve a
clear separation of responsibilities between the different parts of the
application.

Each layer has a specific responsibility and communicates only with the
adjacent layers. This design improves maintainability, extensibility and
readability while reducing dependencies between components.

The architecture separates user interaction, business logic, simulation logic
and database access into independent modules.

### 7.1 Layered Architecture

The application consists of the following layers:

| Layer | Responsibility | Main Components | Owner |
|--------|----------------|-----------------|-------|
| Presentation Layer | Displays information and receives user input via Flask views/templates | ZooView (Flask routes & templates) | Alessio (Frontend) |
| Controller Layer | Coordinates user requests and application flow | ZooController | Darnell (Backend) |
| Service Layer | Contains business logic | ZooService, SimulationService | Darnell (Backend) |
| Domain Layer | Represents the object-oriented zoo model | Animal, Employee, Zoo, Inventory, Enclosure | Darnell (Backend) |
| Simulation Layer | Controls simulation behaviour and scheduled events | SimulationEngine, EventScheduler, EnvironmentalFactor | Darnell (Backend) |
| Repository Layer | Provides an abstraction for database access | Repository Interfaces | Kaiss (Database) |
| Persistence Layer | Stores application data | SQLite, DatabaseConnection | Kaiss (Database) |
| Reporting Layer | Builds and exports CSV/Excel reports from repository data | ReportService | Kaiss (Database) |

### 7.2 Architecture Diagram

The overall system architecture is illustrated in the component and deployment
diagrams in [`Projektplanung/Architecture_System_Diagram.md`](../../Projektplanung/Architecture_System_Diagram.md).

## 8. Object-Oriented Design

The Zoo Management System is designed according to the core principles of
object-oriented programming. These principles provide a modular, maintainable
and extensible software architecture by organizing the application into
independent classes with clearly defined responsibilities.

### 8.1 Abstraction

Abstraction is used to define common behaviour without specifying the exact
implementation.

The abstract base classes `Animal` and `Employee` define the attributes and
methods that all subclasses must implement. These classes cannot be instantiated
directly but serve as templates for specialised classes.

Examples include:

- `Animal`
- `Employee`

---

### 8.2 Inheritance

Inheritance allows subclasses to reuse common functionality from their parent
classes while extending them with specialised behaviour.

The following classes inherit from `Animal`:

- Lion
- Giraffe
- Penguin

The following classes inherit from `Employee`:

- Zookeeper
- Veterinarian
- Administrator

---

### 8.3 Polymorphism

Polymorphism enables different subclasses to be treated through a common
interface.

Although every animal provides the same public methods, each species can
implement them differently.

Examples include:

- `eat()`
- `move()`
- `sleep()`

This allows the simulation to interact with every animal without knowing its
concrete species.

---

### 8.4 Encapsulation

Encapsulation protects the internal state of an object.

Attributes are modified only through controlled methods that perform validation
before updating object data.

Examples include:

- changing health
- changing hunger
- changing energy
- updating inventory quantities
- updating enclosure cleanliness

This ensures that invalid object states cannot occur.

---

### 8.5 Composition and Aggregation

Composition is used when one object is an essential part of another object.

Examples:

- Zoo contains Inventory
- Zoo contains FinanceManager
- Zoo contains Enclosures

Aggregation is used when objects can exist independently.

Examples:

- Enclosures contain Animals.
- Animals can be moved between different Enclosures.
- Employees belong to the Zoo but remain independent objects.

---

### 8.6 SOLID Principles

The software design follows the most important SOLID principles.

**Single Responsibility Principle (SRP)**

Each class has one clearly defined responsibility.

Examples:

- ZooService manages business logic.
- ReportService generates reports (owned by the Database focus, Kaiss).
- SimulationEngine executes simulation steps.

**Open/Closed Principle (OCP)**

The system is designed so that new animal species or employee roles can be added
without modifying existing classes.

**Dependency Inversion Principle (DIP)**

The service layer depends on repository interfaces rather than concrete SQLite
implementations. This makes the persistence layer replaceable with minimal
changes.

## 9. Class Diagram

The class diagram illustrates the static structure of the Zoo Management System.
It shows the relationships between the main domain classes, service classes,
repositories and the database layer.

The diagram is organised according to the layered architecture presented in the
previous chapter and reflects the modular design of the application.

The domain layer contains the central business objects such as `Zoo`,
`Animal`, `Enclosure`, `Inventory` and `Employee`. Specialized animal and
employee classes inherit from their corresponding abstract base classes.

The service layer contains the application logic and coordinates interactions
between the user interface, the domain model and the persistence layer.

Repository interfaces separate the business logic from the SQLite
implementation, allowing the persistence layer to be replaced with minimal
changes.

The class diagram demonstrates the use of object-oriented relationships,
including inheritance, composition, aggregation and associations.

### UML Class Diagram

The complete class diagram is maintained in
[`Projektplanung/Klassendiagramm_Code.md`](../../Projektplanung/Klassendiagramm_Code.md).
Each team member's schwerpunkt-specific view of this diagram is described in
their individual planning document (`planning_backend_darnell.md`,
`planning_frontend_alessio.md`, `planning_db_kaiss.md`).

## 10. Sequence Diagrams

Sequence diagrams illustrate the interaction between the different components
during important application processes.

### 10.1 Animal Feeding

This sequence diagram shows how a feeding request is processed.

The process begins in the user interface. The request is forwarded to the
controller, which calls the service layer. The service validates the request,
updates the animal and inventory data and stores the changes in the database.

See [`Projektplanung/Sequence_AnimalFeeding.md`](../../Projektplanung/Sequence_AnimalFeeding.md) for the full Mermaid sequence diagram.

---

### 10.2 Veterinary Treatment

This sequence diagram illustrates how a veterinarian treats an animal.

The service validates the selected medication, updates the animal's health,
reduces the medication stock and stores the changes in the database.

See [`Projektplanung/Sequence_VeterinaryTreatment.md`](../../Projektplanung/Sequence_VeterinaryTreatment.md) for the full Mermaid sequence diagram.

---

### 10.3 Simulation Step

This sequence diagram describes the execution of one simulation step.

The SimulationService starts the SimulationEngine, which updates environmental
conditions, scheduled events, animal states and enclosure conditions before the
updated state is returned to the user interface.

See [`Projektplanung/Sequence_SimulationStep.md`](../../Projektplanung/Sequence_SimulationStep.md) for the full Mermaid sequence diagram.

## 11. Simulation Design

The Zoo Management System contains a time-based simulation that models the
daily operation of the zoo and the changing state of animals, employees and
enclosures.

The simulation is executed in discrete simulation steps. During each step, the
system updates the state of the zoo according to predefined rules.

### 11.1 Simulation Workflow

Each simulation step performs the following actions:

1. Update environmental conditions.
2. Process scheduled events.
3. Update animal states.
4. Update enclosure conditions.
5. Update inventory and finances if required.
6. Save the updated state.

---

### 11.2 Animal State Updates

During each simulation step, every animal updates its internal attributes.

Examples include:

- Hunger increases over time.
- Energy decreases during activity.
- Animals recover energy while sleeping.
- Health may improve or deteriorate depending on different conditions.
- Age increases according to the simulation time.

---

### 11.3 Environmental Factors

Environmental conditions influence both animals and enclosures.

Possible environmental factors include:

- Temperature
- Weather
- Day/Night cycle

These factors may affect animal behaviour and enclosure conditions.

---

### 11.4 Event Scheduling

The EventScheduler executes planned events automatically during the simulation.

Examples include:

- Feeding time
- Veterinary examinations
- Cleaning enclosures
- Visitor opening hours

Events are executed in chronological order according to the simulation clock.

---

### 11.5 Simulation Engine

The SimulationEngine coordinates the complete simulation process.

Its responsibilities include:

- executing simulation steps
- updating all domain objects
- processing scheduled events
- notifying the service layer when updates are complete

## 12. Database Design

The application stores persistent data in an SQLite database.

The database contains tables representing the main entities of the Zoo
Management System.

Typical entities include:

- Animals
- Enclosures
- Employees
- Inventory
- Food
- Medication
- Financial Transactions
- Scheduled Events

Primary keys uniquely identify each record, while foreign keys define the
relationships between related tables.

The Repository Pattern separates the database implementation from the business
logic, allowing database operations to be performed independently of the domain
model.

### Database Schema

The ER diagram and table definitions (including primary and foreign keys) are
maintained in [`Projektplanung/ER_Diagram_Data_Model.md`](../../Projektplanung/ER_Diagram_Data_Model.md).
See also [`planning_db_kaiss.md`](planning_db_kaiss.md) for the SQLite-specific
schema details.

## 13. Design Patterns

Several software design patterns are applied to improve maintainability,
flexibility and extensibility.

### Repository Pattern

Separates business logic from database access.

### Factory Pattern

Creates objects such as animals and employees without exposing the object
creation process.

### Strategy Pattern

Allows different simulation behaviours or report generation strategies to be
selected without modifying existing code.

### MVC-inspired Structure

The Flask-based web frontend separates presentation, application logic and
data management into different layers.

## 14. Test Plan

The purpose of testing is to verify that all major system functions operate
correctly and that invalid input is handled safely.

The project focuses on documenting representative test cases rather than
implementing automated unit tests.

### 14.1 Testing Strategy

The following aspects will be verified:

- Functional correctness
- Input validation
- Error handling
- Database operations
- Simulation behaviour
- Report generation

### 14.2 Example Test Cases

| Test ID | Feature | Test Description | Expected Result |
|----------|---------|------------------|-----------------|
| TC-01 | Animal Management | Create a new animal | Animal is stored successfully |
| TC-02 | Animal Management | Delete an existing animal | Animal is removed from the database |
| TC-03 | Feeding | Feed an animal with available food | Hunger decreases and inventory is updated |
| TC-04 | Feeding | Feed an animal without available food | Error message is displayed |
| TC-05 | Veterinary Treatment | Treat a sick animal | Health increases and medication stock decreases |
| TC-06 | Simulation | Execute one simulation step | Animal states are updated correctly |
| TC-07 | Inventory | Add inventory item | Inventory quantity increases |
| TC-08 | Finance | Record ticket sale | Financial balance is updated |
| TC-09 | Reports | Generate CSV report | Report file is created successfully |
| TC-10 | Input Validation | Enter invalid values | Validation error is displayed |

## 15. AI Usage and Reflection

Artificial Intelligence was used as a supporting tool throughout the planning
and development of the project.

AI assisted in:

- brainstorming software architecture
- discussing object-oriented design
- improving documentation
- reviewing code
- generating UML and Mermaid diagrams
- identifying potential improvements

All AI-generated content was reviewed, evaluated and adapted by the project
team before being incorporated into the final project.

The responsibility for the correctness and quality of the software remains with
the project team.

## 16. References

The following resources were used during the project:

- Python Software Foundation. Python Documentation.
- SQLite Documentation.
- Mermaid Documentation.
- Pandas Documentation.
- OpenPyXL Documentation.
- Fowler, M. *Patterns of Enterprise Application Architecture.*
- Gamma, E., Helm, R., Johnson, R., & Vlissides, J. *Design Patterns.*

## 17. Appendix

The appendix contains supplementary material supporting the project
documentation.

Possible contents include:

- Complete UML class diagram
- Sequence diagrams
- Entity Relationship Diagram
- Folder structure
- Example database schema
- Sample reports
- Screenshots

