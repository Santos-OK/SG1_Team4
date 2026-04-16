"""
Battery Component
Stores energy from solar panels and supplies it when needed.
"""


class Battery:
    def __init__(self, cfg: dict, count: int = 1):
        self.count = count
        self.capacity       = cfg["capacity_kwh"] * count
        self.min_soc        = cfg["min_soc_percent"]
        self.max_soc        = cfg["max_soc_percent"]
        self.efficiency     = cfg["efficiency"]
        self.current_soc    = cfg["initial_soc_percent"]

        # Stats
        self.total_charged    = 0.0
        self.total_discharged = 0.0
        self.charge_cycles    = 0
        self.discharge_cycles = 0
        self.full_events      = 0
        self.empty_events     = 0

    # ------------------------------------------------------------------ #
    def get_current_energy(self) -> float:
        return (self.current_soc / 100.0) * self.capacity

    def charge(self, energy_kwh: float) -> float:
        effective = energy_kwh * self.efficiency
        current   = self.get_current_energy()
        max_e     = (self.max_soc / 100.0) * self.capacity
        space     = max_e - current
        actual    = min(effective, space)

        if actual > 0:
            self.current_soc   = ((current + actual) / self.capacity) * 100.0
            self.total_charged += actual
            self.charge_cycles += 1
            if self.is_full():
                self.full_events += 1
        return actual

    def discharge(self, energy_kwh: float) -> float:
        current   = self.get_current_energy()
        min_e     = (self.min_soc / 100.0) * self.capacity
        available = current - min_e
        actual    = min(energy_kwh, available)
        effective = actual * self.efficiency

        if actual > 0:
            self.current_soc      = ((current - actual) / self.capacity) * 100.0
            self.total_discharged += effective
            self.discharge_cycles += 1
            if self.is_empty():
                self.empty_events += 1
        return effective

    def is_full(self)  -> bool: return self.current_soc >= self.max_soc
    def is_empty(self) -> bool: return self.current_soc <= self.min_soc

    def get_status(self) -> dict:
        return {
            "count":            self.count,
            "soc_percent":      round(self.current_soc, 2),
            "energy_kwh":       round(self.get_current_energy(), 2),
            "capacity_kwh":     self.capacity,
            "is_full":          self.is_full(),
            "is_empty":         self.is_empty(),
            "total_charged":    round(self.total_charged, 2),
            "total_discharged": round(self.total_discharged, 2),
            "charge_cycles":    self.charge_cycles,
            "full_events":      self.full_events,
            "empty_events":     self.empty_events,
        }