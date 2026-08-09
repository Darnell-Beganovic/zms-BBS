"""EventScheduler: manages time-triggered simulation events.

Schwerpunkt: Backend (Simulation Layer) - Darnell Beganovic
"""

from __future__ import annotations

from typing import Any


class EventScheduler:
    """EventScheduler - a simple time-triggered event queue.

    Deliberately generic: an "event" is just a dict, and EventScheduler
    never interprets its contents beyond an optional `"action"` key. If
    present and callable, `execute_due_events()` calls it with no
    arguments; if absent, the event is simply removed once due. This
    keeps EventScheduler reusable for any kind of event (feeding times,
    enclosure cleaning, ...) without depending on Animal/Enclosure/Zoo
    itself, matching aufgabe.md's description of it as "eine einfache
    Klasse, die zeitgesteuerte Ereignisse verwalten kann."

        - Constructor: stores all attributes privately.
        - _scheduled_events (list[dict]): pending entries, each
          `{"event": dict, "trigger_time": int}`.
    """

    def __init__(self) -> None:
        """Create an EventScheduler with an empty pending queue.

        Test:
            - When the constructor is called, then `get_due_events(0)`
              returns an empty list.
        """
        self._scheduled_events: list[dict[str, Any]] = []

    def schedule_event(self, event: dict[str, Any], trigger_time: int) -> None:
        """Queue an event to become due at the given simulation time.

        Args:
            event (dict): arbitrary event payload. If it contains an
                `"action"` key with a callable value, that callable is
                invoked (with no arguments) once the event becomes due
                and is executed.
            trigger_time (int): the simulation time (matching
                `SimulationEngine.current_step`) at which this event
                becomes due.

        Test:
            - Given an empty scheduler, when `schedule_event({"type":
              "feed"}, 5)` is called, then `get_due_events(5)` returns a
              list containing that event.
            - Given trigger_time=10, when `get_due_events(5)` is called
              afterwards, then the event is not yet due (empty list).
        """
        self._scheduled_events.append({"event": event, "trigger_time": trigger_time})

    def get_due_events(self, current_time: int) -> list[dict[str, Any]]:
        """List every pending event whose trigger time has passed, without removing them.

        Args:
            current_time (int): the current simulation time.

        Returns:
            list[dict]: the `event` payloads (not the wrapper entries)
                for every scheduled event with `trigger_time <=
                current_time`, in the order they were scheduled.

        Test:
            - Given events scheduled at trigger_time=3 and trigger_time=7,
              when `get_due_events(5)` is called, then only the
              trigger_time=3 event is returned.
            - Given no events are scheduled, when `get_due_events()` is
              called, then an empty list is returned, not None.
        """
        return [
            entry["event"]
            for entry in self._scheduled_events
            if entry["trigger_time"] <= current_time
        ]

    def execute_due_events(self, current_time: int) -> None:
        """Execute and remove every event whose trigger time has passed.

        Args:
            current_time (int): the current simulation time.

        Test:
            - Given an event with an `"action"` callable scheduled at
              trigger_time=3, when `execute_due_events(5)` is called,
              then the callable is invoked exactly once and the event no
              longer appears in `get_due_events()` afterwards.
            - Given an event scheduled at trigger_time=10, when
              `execute_due_events(5)` is called, then it stays pending
              (not yet due) and is not removed.
        """
        due, pending = [], []
        for entry in self._scheduled_events:
            (due if entry["trigger_time"] <= current_time else pending).append(entry)

        self._scheduled_events = pending
        for entry in due:
            action = entry["event"].get("action")
            if callable(action):
                action()
