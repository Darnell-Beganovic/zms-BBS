"""Veterinarian employee: examines and treats animals.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zoo_simulation.domain.employees.employee import Employee

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal
    from zoo_simulation.domain.medication import Medication

_MEDICATION_DOSE = 1.0
_HEALTH_GAIN = 20
_SICK_THRESHOLD = 40


class Veterinarian(Employee):
    """Veterinarian - examines and treats sick or injured animals."""

    def perform_task(self) -> str:
        """Describe this employee's daily routine. Pure, no side effects.

        Returns:
            str: a human-readable description.

        Test:
            - When `perform_task()` is called, then it returns a
              non-empty string mentioning examining/treating animals.
            - When called twice, then it returns the same string both
              times (pure, no state change) - actual examination/
              treatment happens via `examine_animal()`/`treat_animal()`
              instead.
        """
        return "Examines and treats sick or injured animals."

    def examine_animal(self, animal: Animal) -> str:
        """Diagnose an animal's condition from its current health.

        Args:
            animal (Animal): the animal to examine.

        Returns:
            str: "sick" if `health` is below the sick threshold,
                "healthy" otherwise.

        Test:
            - Given an animal with health=30, when
              `examine_animal(animal)` is called, then it returns "sick".
            - Given an animal with health=90, when
              `examine_animal(animal)` is called, then it returns
              "healthy".
        """
        return "sick" if animal.health < _SICK_THRESHOLD else "healthy"

    def treat_animal(self, animal: Animal, medication: Medication) -> None:
        """Treat an animal with medication, improving its health.

        Args:
            animal (Animal): the animal to treat.
            medication (Medication): the medication to use.

        Test:
            - Given a sick animal with health=30 and Medication with
              enough quantity, when `treat_animal(animal, medication)`
              is called, then the animal's health increases by 20 and
              the medication's quantity decreases.
            - Given a healthy animal with health=100, when
              `treat_animal()` is called, then health is clamped at 100
              (no overflow, via `Animal.adjust_health()`).
        """
        if medication.decrease_quantity(_MEDICATION_DOSE):
            animal.adjust_health(_HEALTH_GAIN)
