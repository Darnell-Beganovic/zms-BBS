"""behavior.py - abstract base class for behaviors composed into an Animal.

Schwerpunkt: Backend (Domain Layer) - Darnell Beganovic
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoo_simulation.domain.animals.animal import Animal


class Behavior(ABC):
    """Behavior - one behavior pattern an Animal is composed of.

    Animal *-- "1..*" Behavior (composition, see
    ../../Projektplanung/Klassendiagramm_Code.md): each Animal owns a
    small list of Behavior instances, and Animal.update() calls
    execute(self) on every one of them once per simulation tick.
    Deliberately kept simple: each concrete Behavior affects exactly one
    Animal stat in isolation (see FeedingBehavior/SocialBehavior/
    RestBehavior), there is no blending or interaction between multiple
    Behaviors on the same Animal.
    """

    @abstractmethod
    def execute(self, animal: Animal) -> None:
        """Apply this behavior's effect to the given animal.

        Args:
            animal (Animal): the animal this behavior is composed into.
                Implementations mutate the animal's state through its
                public methods only, never its private attributes
                directly.

        Test:
            - See the concrete subclasses (FeedingBehavior,
              SocialBehavior, RestBehavior) for concrete Given/When/Then
              cases; this method has no behavior of its own to test.
        """
        raise NotImplementedError
