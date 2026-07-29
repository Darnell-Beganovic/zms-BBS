## Sequence Diagram — Animal Feeding

Sequence diagram showing the feeding flow (Zookeeper → ZooView → ZooController → ZooService → Repositories → Animal / FoodItem).

```mermaid
sequenceDiagram
    actor Zookeeper
    participant View as ZooView
    participant Controller as ZooController
    participant Service as ZooService
    participant AnimalRepo as AnimalRepository
    participant InventoryRepo as InventoryRepository
    participant Animal
    participant Food as FoodItem

    Zookeeper->>View: Select animal and food
    View->>Controller: feed_animal(animal_id, food_id)
    Controller->>Service: feed_animal(animal_id, food_id)

    Service->>AnimalRepo: get_by_id(animal_id)
    AnimalRepo-->>Service: Animal

    Service->>InventoryRepo: get_food_item(food_id)
    InventoryRepo-->>Service: FoodItem

    Service->>Food: decrease_quantity(amount)
    Food-->>Service: quantity updated

    Service->>Animal: eat(FoodItem)
    Animal-->>Service: hunger reduced

    Service->>AnimalRepo: update(Animal)
    Service->>InventoryRepo: update_food_item(FoodItem)

    Service-->>Controller: feeding successful
    Controller-->>View: display confirmation
```

Hinweis: Möchtest du, dass ich diese Datei in `Projektplanung/UserStories_UseCases.md` verlinke oder gleich weitere Sequenzdiagramme erstelle?