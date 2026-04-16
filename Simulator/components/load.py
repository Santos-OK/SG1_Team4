"""
Load Component
models the energy demand of a household.
"""

import random
import simpy


class Load:
    def __init__(self, household_cfg: dict, wealth_multipliers: dict, env: simpy.Environment):
        self.env = env  

        # get wealth level and apply multiplier to adjust consumption
        wealth = household_cfg["wealth"]
        multiplier = wealth_multipliers.get(wealth, 1.0)

        # basic load parameters
        self.base_load   = household_cfg["base_load_kw"]  * multiplier   # constant base consumption
        self.peak_spike  = household_cfg["peak_spike_kw"] * multiplier   # extra demand during peaks
        self.peak_start  = household_cfg["peak_hours_start"]             # start of peak hours
        self.peak_end    = household_cfg["peak_hours_end"]               # end of peak hours
        self.variability = household_cfg["load_variability"]             # randomness 

        # extra demand from random appliance usage
        self._extra_spike_kw = 0.0
        self.env.process(self._random_appliance_events())  # start the process

        # stats to track consumption 
        self.total_consumed = 0.0
        self.peak_demand    = 0.0
        self.unmet_events   = 0
        self.total_unmet    = 0.0

    # ------------------------------------------------------------------ #
    def _random_appliance_events(self):
        """
        This runs as a separate process.
        It randomly turns appliances on and off to create sudden demand spikes.
        """
        while True:
            # wait a random time (between 0.5 and 4)
            wait = random.uniform(0.5, 4.0)
            yield self.env.timeout(wait)

            # Generate a random spike and duration
            spike    = random.uniform(0, self.peak_spike * 0.4)
            duration = random.uniform(0.25, 1.5)  # between ~15 min and 1.5 hours

            # Activate extra demand
            self._extra_spike_kw = spike

            yield self.env.timeout(duration)

            self._extra_spike_kw = 0.0

    def get_demand(self, hour_of_day: int) -> float:
        """Returns the current energy demand in kW."""
        
        # Start with base load + some randomness
        demand = self.base_load + random.uniform(0, self.base_load * self.variability)

        # add extra demand during peak hours 
        if self.peak_start <= hour_of_day <= self.peak_end:
            demand += random.uniform(0, self.peak_spike)

        # Add random appliance spike (from the other process)
        demand += self._extra_spike_kw

        # Track highest demand reached
        if demand > self.peak_demand:
            self.peak_demand = demand

        return demand

    def consume(self, kwh: float):
        # add consumed energy to total
        self.total_consumed += kwh

    def record_unmet(self, kwh: float):
        # Track energy not supplied
        if kwh > 0:
            self.unmet_events += 1
            self.total_unmet  += kwh

    def get_status(self) -> dict:
        # Returnsummary of the current load 
        return {
            "base_load_kw":        round(self.base_load, 3),
            "peak_demand_kw":      round(self.peak_demand, 3),
            "total_consumed_kwh":  round(self.total_consumed, 2),
            "unmet_events":        self.unmet_events,
            "total_unmet_kwh":     round(self.total_unmet, 2),
        }