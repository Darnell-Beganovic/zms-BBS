"""EnvironmentalFactor: models weather and time-of-day influences on animals.

Schwerpunkt: Backend (Simulation Layer) - Darnell Beganovic
"""

from __future__ import annotations


class EnvironmentalFactor:
    """EnvironmentalFactor - current environmental conditions in the zoo.

        - Constructor: stores all attributes privately. Unlike FoodItem's
          quantity, these attributes represent a snapshot of "now" that
          SimulationEngine is expected to replace with a fresh
          EnvironmentalFactor each tick (rather than mutating this one),
          so no setters are provided here either.
        - _temperature (float): degrees, e.g. Celsius.
        - _time_of_day (str): e.g. "day" or "night".
        - _weather_condition (str): e.g. "sunny", "rainy", "storm".
    """

    def __init__(
        self,
        temperature: float = 20.0,
        time_of_day: str = "day",
        weather_condition: str = "sunny",
    ) -> None:
        """Create an EnvironmentalFactor snapshot.

        Args:
            temperature (float, optional): degrees. Defaults to 20.0.
            time_of_day (str, optional): "day" or "night". Defaults to
                "day".
            weather_condition (str, optional): e.g. "sunny", "rainy",
                "storm". Defaults to "sunny".

        Test:
            - Given temperature=35.0 and weather_condition="storm", when
              the constructor is called, then `.temperature` is 35.0 and
              `.weather_condition` is "storm".
            - Given no arguments, when the constructor is called, then
              `.time_of_day` is "day" (default).
        """
        self._temperature = temperature
        self._time_of_day = time_of_day
        self._weather_condition = weather_condition

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def time_of_day(self) -> str:
        return self._time_of_day

    @property
    def weather_condition(self) -> str:
        return self._weather_condition

    def get_influence_factor(self) -> float:
        """Compute a single multiplier summarizing how favorable conditions are.

        1.0 means neutral/favorable conditions; values below 1.0 model
        conditions that make animal behavior less effective (e.g. resting
        less restfully during a storm, moving less at night). Kept
        deliberately simple - a small set of independent penalties
        multiplied together, no cross-factor interaction terms.

        Returns:
            float: multiplier in the range (0.0, 1.0], intended to scale
                effects such as `Behavior.execute()` outcomes.

        Test:
            - Given weather_condition="sunny" and time_of_day="day", when
              `get_influence_factor()` is called, then it returns 1.0
              (fully favorable).
            - Given weather_condition="storm", when
              `get_influence_factor()` is called, then it returns a value
              less than 1.0 (storm penalty applied).
        """
        factor = 1.0
        if self._weather_condition == "storm":
            factor *= 0.5
        elif self._weather_condition == "rainy":
            factor *= 0.8
        if self._time_of_day == "night":
            factor *= 0.9
        return factor
