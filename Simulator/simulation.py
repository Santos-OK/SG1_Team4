"""
GreenGrid Simulation Engine
Runs a neighborhood-level simulation with multiple households simultaneously.
Each household has its own SimPy processes (inverter failure, load events)
running concurrently — properly exploiting SimPy's event-driven model.
"""

import simpy
import random
from pathlib import Path
from components import Battery, SolarPanel, Inverter, Load, Grid
from utils import get_daily_cloud_coverage


# ═══════════════════════════════════════════════════════════════════════════ #
class HouseholdSim:
    """
    Represents a single household running inside the shared SimPy environment.
    All its sub-processes (inverter faults, appliance spikes) are concurrent.
    """

    def __init__(self, env: simpy.Environment, household_cfg: dict, shared_cfg: dict):
        self.env   = env
        self.hcfg  = household_cfg
        self.id    = household_cfg["id"]
        self.htype = household_cfg["type"]
        self.wealth = household_cfg["wealth"]

        # Components
        bat_count = shared_cfg["battery"]["count"] if household_cfg.get("has_battery") else 0
        self.battery  = Battery(shared_cfg["battery"], count=max(bat_count, 1)) \
                        if household_cfg.get("has_battery") else None
        self.solar    = SolarPanel(shared_cfg["solar"]) \
                        if household_cfg.get("has_solar") else None
        self.inverter = Inverter(shared_cfg["inverter"], env) \
                        if household_cfg.get("has_solar") else None
        self.load     = Load(household_cfg, shared_cfg["wealth_multipliers"], env)
        self.grid     = Grid(shared_cfg["grid"])

        self.strategy      = shared_cfg["simulation"]["energy_management_strategy"]
        self.time_step_h   = shared_cfg["simulation"]["time_step_minutes"] / 60.0

        # Shared cloud coverage (set by NeighborhoodSim each day)
        self.cloud_coverage = 0.0

        # Data log for this household
        self.log: list[dict] = []

    # ------------------------------------------------------------------ #
    def tick(self, hour_abs: float):
        """Called every time step by the neighborhood coordinator."""
        hour_of_day = int(hour_abs % 24)
        day         = int(hour_abs // 24) + 1

        # ── Solar generation ──────────────────────────────────────────── #
        solar_kw = 0.0
        if self.solar and self.inverter:
            solar_kw = self.solar.generate(
                hour_of_day,
                self.cloud_coverage,
                self.inverter.is_operational(),
                self.inverter.max_output,
            )
        solar_kwh = solar_kw * self.time_step_h

        # ── Load demand ───────────────────────────────────────────────── #
        load_kw  = self.load.get_demand(hour_of_day)
        load_kwh = load_kw * self.time_step_h

        # ── Energy management ─────────────────────────────────────────── #
        grid_import_kwh, grid_export_kwh = self._manage(solar_kwh, load_kwh)

        self.load.consume(load_kwh)

        # ── Log ───────────────────────────────────────────────────────── #
        bat_soc = self.battery.current_soc if self.battery else None
        inv_ok  = self.inverter.is_operational() if self.inverter else True

        self.log.append({
            "hour":              hour_abs,
            "day":               day,
            "hour_of_day":       hour_of_day,
            "household_id":      self.id,
            "household_type":    self.htype,
            "wealth":            self.wealth,
            "solar_kw":          round(solar_kw,      3),
            "load_kw":           round(load_kw,       3),
            "solar_kwh":         round(solar_kwh,     3),
            "load_kwh":          round(load_kwh,      3),
            "grid_import_kwh":   round(grid_import_kwh, 3),
            "grid_export_kwh":   round(grid_export_kwh, 3),
            "battery_soc":       round(bat_soc, 2) if bat_soc is not None else None,
            "cloud_coverage":    round(self.cloud_coverage, 3),
            "inverter_ok":       inv_ok,
            "net_load_kw":       round(load_kw - solar_kw, 3),   # for duck curve
        })

    # ------------------------------------------------------------------ #
    def _manage(self, solar_kwh: float, load_kwh: float):
        """Dispatch to the configured energy management strategy."""
        strategies = {
            "LOAD_PRIORITY":    self._load_priority,
            "CHARGE_PRIORITY":  self._charge_priority,
            "PRODUCE_PRIORITY": self._produce_priority,
        }
        fn = strategies.get(self.strategy, self._load_priority)
        return fn(solar_kwh, load_kwh)

    def _load_priority(self, solar_kwh, load_kwh):
        rem_solar = solar_kwh
        rem_load  = load_kwh
        imp = exp = 0.0

        # 1. Solar → load
        to_load    = min(rem_solar, rem_load)
        rem_solar -= to_load;  rem_load -= to_load

        # 2. Battery → remaining load
        if rem_load > 0 and self.battery:
            rem_load -= self.battery.discharge(rem_load)

        # 3. Grid → remaining load
        if rem_load > 0:
            imp = self.grid.import_energy(rem_load);  rem_load = 0

        # 4. Excess solar → battery
        if rem_solar > 0 and self.battery:
            charged    = self.battery.charge(rem_solar)
            rem_solar -= charged

        # 5. Excess solar → grid
        if rem_solar > 0:
            exp = self.grid.export_energy(rem_solar)

        if rem_load > 0: self.load.record_unmet(rem_load)
        return imp, exp

    def _charge_priority(self, solar_kwh, load_kwh):
        rem_solar = solar_kwh
        rem_load  = load_kwh
        imp = exp = 0.0

        # 1. Solar → battery first
        if self.battery:
            charged    = self.battery.charge(rem_solar)
            rem_solar -= charged

        # 2. Remaining solar → load
        to_load    = min(rem_solar, rem_load)
        rem_solar -= to_load;  rem_load -= to_load

        # 3. Battery → load
        if rem_load > 0 and self.battery:
            rem_load -= self.battery.discharge(rem_load)

        # 4. Grid → load
        if rem_load > 0:
            imp = self.grid.import_energy(rem_load);  rem_load = 0

        # 5. Export excess
        if rem_solar > 0:
            exp = self.grid.export_energy(rem_solar)

        if rem_load > 0: self.load.record_unmet(rem_load)
        return imp, exp

    def _produce_priority(self, solar_kwh, load_kwh):
        rem_solar = solar_kwh
        rem_load  = load_kwh
        imp = exp = 0.0

        # 1. Export first
        exp        = self.grid.export_energy(rem_solar)
        rem_solar -= exp

        # 2. Charge battery
        if rem_solar > 0 and self.battery:
            charged    = self.battery.charge(rem_solar)
            rem_solar -= charged

        # 3. Solar → load
        to_load    = min(rem_solar, rem_load)
        rem_load  -= to_load

        # 4. Battery → load
        if rem_load > 0 and self.battery:
            rem_load -= self.battery.discharge(rem_load)

        # 5. Grid import
        if rem_load > 0:
            imp = self.grid.import_energy(rem_load)

        if rem_load > 0: self.load.record_unmet(rem_load)
        return imp, exp

    # ------------------------------------------------------------------ #
    def get_summary(self) -> dict:
        summary = {
            "household_id":   self.id,
            "household_type": self.htype,
            "wealth":         self.wealth,
            "strategy":       self.strategy,
            "load":           self.load.get_status(),
            "grid":           self.grid.get_status(),
        }
        if self.solar:    summary["solar"]    = self.solar.get_status()
        if self.battery:  summary["battery"]  = self.battery.get_status()
        if self.inverter: summary["inverter"] = self.inverter.get_status()
        return summary


# ═══════════════════════════════════════════════════════════════════════════ #
class NeighborhoodSim:
    """
    Coordinates all households in the neighborhood.
    One SimPy environment drives every household's concurrent sub-processes.
    """

    def __init__(self, cfg: dict):
        self.cfg         = cfg
        self.sim_cfg     = cfg["simulation"]
        self.cloud_cfg   = cfg["cloud_coverage"]
        self.total_hours = self.sim_cfg["days"] * 24
        self.time_step_h = self.sim_cfg["time_step_minutes"] / 60.0
        self.season      = self.sim_cfg["season"]
        self.verbose     = self.sim_cfg.get("verbose", False)

        # Single shared SimPy environment
        self.env = simpy.Environment()

        # Instantiate all households
        self.households: list[HouseholdSim] = [
            HouseholdSim(self.env, hcfg, cfg)
            for hcfg in cfg["households"]
        ]

        self.neighborhood_log: list[dict] = []

    # ------------------------------------------------------------------ #
    def run(self) -> list[dict]:
        """Start the simulation and return the full neighborhood log."""
        self.env.process(self._coordinator())
        self.env.run(until=self.total_hours)
        return self.neighborhood_log

    def _coordinator(self):
        """
        Master SimPy generator: advances time and calls tick() on every
        household. Each household's inverter and load sub-processes run
        concurrently within the same environment.
        """
        current_day     = -1
        cloud_coverage  = 0.0
        hour            = 0.0

        while hour < self.total_hours:
            day = int(hour // 24)

            # New day → new shared cloud coverage (same solar conditions for neighborhood)
            if day != current_day:
                current_day    = day
                cloud_coverage = get_daily_cloud_coverage(self.season, self.cloud_cfg)
                if self.verbose:
                    print(f"Day {day+1:>3} | clouds: {cloud_coverage:.0%}")

            # Push cloud coverage to every household
            for h in self.households:
                h.cloud_coverage = cloud_coverage

            # Tick every household
            for h in self.households:
                h.tick(hour)

            # Aggregate neighborhood snapshot
            self._log_neighborhood(hour, day + 1)

            yield self.env.timeout(self.time_step_h)
            hour += self.time_step_h

    def _log_neighborhood(self, hour: float, day: int):
        """Appends an aggregated neighborhood record."""
        total_solar  = sum(h.log[-1]["solar_kw"]        for h in self.households if h.log)
        total_load   = sum(h.log[-1]["load_kw"]         for h in self.households if h.log)
        total_import = sum(h.log[-1]["grid_import_kwh"] for h in self.households if h.log)
        total_export = sum(h.log[-1]["grid_export_kwh"] for h in self.households if h.log)
        cloud        = self.households[0].cloud_coverage if self.households else 0

        self.neighborhood_log.append({
            "hour":          hour,
            "day":           day,
            "hour_of_day":   int(hour % 24),
            "total_solar_kw":  round(total_solar,  3),
            "total_load_kw":   round(total_load,   3),
            "net_load_kw":     round(total_load - total_solar, 3),
            "total_import_kwh": round(total_import, 3),
            "total_export_kwh": round(total_export, 3),
            "cloud_coverage":   round(cloud, 3),
        })

    # ------------------------------------------------------------------ #
    def get_all_household_logs(self) -> list[dict]:
        """Returns every time-step record from every household."""
        combined = []
        for h in self.households:
            combined.extend(h.log)
        return combined

    def get_summaries(self) -> list[dict]:
        return [h.get_summary() for h in self.households]