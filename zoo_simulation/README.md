# zoo_simulation

This folder contains the actual Python source code of the Zoo Management
System (ZMS). For the full project overview, team members, tech stack and
installation instructions, see the [repository root README](../README.md).

## Documentation

Detailed planning and design documentation lives in [`docs/`](docs):

| Document | Description |
|----------|-------------|
| [`planning.md`](docs/planning.md) | Shared project planning: scope, architecture, domain model, simulation design |
| [`planning_backend_darnell.md`](docs/planning_backend_darnell.md) | Individual planning — Backend (Darnell Beganovic) |
| [`planning_frontend_alessio.md`](docs/planning_frontend_alessio.md) | Individual planning — Frontend (Alessio Bellamacina) |
| [`planning_db_kaiss.md`](docs/planning_db_kaiss.md) | Individual planning — Database (Kaiss Saleh) |
| [`ai_reflection.md`](docs/ai_reflection.md) | Reflection on the use of AI during development |

The Mermaid diagrams referenced throughout these documents (class diagram,
ER diagram, sequence diagrams, architecture) are maintained in
[`../Projektplanung/`](../Projektplanung) at the repository root.

## Running the Application

From this folder:

```bash
pip install -r requirements.txt
python main.py
```
