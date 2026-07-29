## Sequence Diagram — Simulation Step

Sequence diagram showing a single simulation step flow (User → ZooView → ZooController → SimulationService → SimulationEngine → EventScheduler/Environment → domain objects).

```mermaid
sequenceDiagram
    actor User
    participant View as ZooView
    participant Controller as ZooController
    participant Service as SimulationService
    participant Engine as SimulationEngine
    participant Scheduler as EventScheduler
    participant Environment as EnvironmentalFactor
    participant Zoo
    participant Enclosure
    participant Animal
    participant ZooRepo as ZooRepository

    User->>View: Start simulation step
    View->>Controller: run_simulation_step()
    Controller->>Service: run_step()

    Service->>Engine: tick()

    Engine->>Scheduler: get_due_events(current_time)
    Scheduler-->>Engine: scheduled events

    Engine->>Environment: update()
    Environment-->>Engine: current conditions

    loop For each enclosure
        Engine->>Enclosure: update(Environment)
    end

    loop For each animal
        Engine->>Animal: update_state(Environment)
        Animal-->>Engine: updated state
    end

    Engine->>Scheduler: execute_due_events()
    Scheduler-->>Engine: events completed

    Engine->>Zoo: calculate_average_welfare()
    Zoo-->>Engine: welfare value

    Engine-->>Service: updated zoo state
    Service->>ZooRepo: save(Zoo)
    ZooRepo-->>Service: save successful

    Service-->>Controller: simulation result
    Controller-->>View: display updated status
```

Note: Soll ich diese Datei in `Projektplanung/UserStories_UseCases.md` verlinken oder weitere Sequenzdiagramme erstellen?