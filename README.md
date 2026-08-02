# Zoo Management System (ZMS)

The Zoo Management System (ZMS) is a Python-based software project that simulates the management and daily operation of a zoo using object-oriented programming principles.

The application combines administrative functionality, animal management and a time-based simulation within a modular software architecture. The project is developed as part of the *Programming II* module.

---

# Team Members & Responsibilities

| Member | Focus Area | Individual Planning |
|--------|-----------|----------------------|
| Kaiss Saleh | Database (SQLite, Repository Pattern, reports) | [`planning_db_kaiss.md`](zoo_simulation/docs/planning_db_kaiss.md) |
| Alessio Bellamacina | Frontend (Flask web UI) | [`planning_frontend_alessio.md`](zoo_simulation/docs/planning_frontend_alessio.md) |
| Darnell Beganovic | Backend (domain model, services, simulation) | [`planning_backend_darnell.md`](zoo_simulation/docs/planning_backend_darnell.md) |

Architecture, integration, code review and documentation remain shared
responsibilities across the whole team; see
[`zoo_simulation/docs/planning.md`](zoo_simulation/docs/planning.md) for details.

---

# Project Features

The Zoo Management System includes the following core features:

- Animal management
- Enclosure management
- Employee management
- Inventory management
- Financial management
- Time-based zoo simulation
- Event scheduling
- SQLite database persistence
- CSV report generation
- Excel report generation
- Modular object-oriented architecture

---

# Technology Stack

| Technology | Purpose |
|------------|---------|
| Python 3.14 | Programming language |
| Flask | Web frontend / routing |
| SQLite | Database |
| sqlite3 | Database access |
| pandas | Data processing |
| openpyxl | Excel export |
| csv | CSV export |
| pytest | Testing (test cases described, see docs) |
| Git | Version control |

---

# Project Structure

```text
zoo_simulation/
│
├── controller/
├── database/
├── docs/
├── domain/
├── exports/
├── frontend/
├── repositories/
├── services/
├── simulation/
├── tests/
│
├── main.py
├── requirements.txt
└── README.md
```

---

# Installation

Clone the repository:

```bash
git clone <repository-url>
```

Navigate to the project directory:

```bash
cd zoo_simulation
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

# Running the Application

Start the application using:

```bash
python main.py
```

---

# Documentation

Detailed project documentation is available in the `docs` folder.

| Document | Description |
|----------|-------------|
| planning.md | Project planning, architecture and design |
| test_plan.md | Test strategy and planned test cases |
| ai_reflection.md | Reflection on the use of AI during development |

---

# Project Status

Current Status:

- ✅ Planning completed
- 🚧 Implementation in progress
- ⏳ Testing planned

---

# AI Usage

Artificial intelligence tools are used to support software development and documentation.

All AI-generated content is manually reviewed, validated and adapted by the project team before being incorporated into the final project.

---

# License

This project was developed for educational purposes as part of the Programming II module.