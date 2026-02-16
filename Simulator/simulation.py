"""
This file contains the main logic that coordinates all components
and executes the simulation step by step.
"""

import simpy
import random
import pandas as pd
import config
import utils
from components import Battery, SolarPanel, Inverter, Load, Grid


class GreenGridSimulation:
    """
    
    What does this class do?
    ------------------------
    - Creates all components (battery, panels, etc.)
    - Executes the simulation step by step
    - Decides how energy flows according to the configured strategy
    - Records all data for later analysis
    """
    
    def __init__(self):
        # Create SimPy environment
        self.env = simpy.Environment()
        
        # Create components
        self.battery = Battery(count=config.BATTERY_COUNT)
        self.solar = SolarPanel()
        self.inverter = Inverter()
        self.load = Load()
        self.grid = Grid()
        
        # Simulation state
        self.current_day = 1
        self.daily_cloud_coverage = utils.get_daily_cloud_coverage(config.SEASON)
        
        # Data for logging
        self.data_log = []
        
        # Time configuration
        self.time_step_hours = config.TIME_STEP_MINUTES / 60.0
        self.total_hours = config.SIMULATION_DAYS * 24
        
        print("=" * 70)
        print("🌞 GREENGRID SIMULATION STARTED 🔋")
        print("=" * 70)
        print(f"Strategy: {config.ENERGY_MANAGEMENT_STRATEGY}")
        print(f"Duration: {config.SIMULATION_DAYS} days")
        print(f"Season: {config.SEASON}")
        print(f"Time step: {config.TIME_STEP_MINUTES} minutes")
        print(f"Batteries: {config.BATTERY_COUNT} x {config.BATTERY_CAPACITY} kWh")
        print("=" * 70)
    
    def run(self):
        """
        Executes the complete simulation.
        
        Explanation:
        ------------
        SimPy uses "processes" that run in simulated time.
        We create a process that runs at each time step.
        """
        # Register the simulation process in SimPy
        self.env.process(self.simulate())
        
        # Run until final time
        self.env.run(until=self.total_hours)
        
        print("\n" + "=" * 70)
        print("✅ SIMULATION COMPLETED")
        print("=" * 70)
        
        # Generate summary
        self.print_summary()
        
        # Export data
        self.export_data()
    
    def simulate(self):
        """
        Main simulation process that runs at each time step.
        
        This is the heart of the simulation. At each step:
        1. Calculates solar generation
        2. Calculates house demand
        3. Decides how to distribute energy
        4. Records data
        5. Advances to the next step
        """
        current_hour = 0
        
        while current_hour < self.total_hours:
            # Calculate day and hour
            day = int(current_hour // 24) + 1
            hour_of_day = int(current_hour % 24)
            
            # If it's a new day, generate new cloud coverage
            if day != self.current_day:
                self.current_day = day
                self.daily_cloud_coverage = utils.get_daily_cloud_coverage(config.SEASON)
                if config.VERBOSE:
                    print(f"\n--- Day {day} started (Clouds: {self.daily_cloud_coverage:.1%}) ---")
            
            # Update inverter (can fail or recover)
            self.inverter.update(self.time_step_hours)
            
            # Generate solar energy
            solar_power_kw = self.solar.generate(
                hour_of_day,
                self.daily_cloud_coverage,
                self.inverter.is_operational
            )
            
            # Apply inverter limit
            solar_power_kw = self.solar.apply_inverter_limit(solar_power_kw)
            
            # Convert power (kW) to energy (kWh) according to time step
            solar_energy_kwh = solar_power_kw * self.time_step_hours
            
            # Get house demand
            load_power_kw = self.load.get_demand(hour_of_day)
            load_energy_kwh = load_power_kw * self.time_step_hours
            
            # ENERGY MANAGEMENT - this is where we decide what to do
            self.manage_energy_flow(solar_energy_kwh, load_energy_kwh)
            
            # Record data for this step
            self.log_data(current_hour, hour_of_day, solar_power_kw, load_power_kw)
            
            # Print status (every hour if VERBOSE is active)
            if config.VERBOSE and hour_of_day == 12:  # Only at noon to avoid saturation
                self.print_status(current_hour, solar_power_kw, load_power_kw)
            
            # Wait until next step (this is SimPy)
            yield self.env.timeout(self.time_step_hours)
            
            # Advance time
            current_hour += self.time_step_hours
    
    def manage_energy_flow(self, solar_kwh, load_kwh):
        """
        Manages energy flow according to the configured strategy.
        
        Parameters:
        -----------
        solar_kwh : float
            Energy generated by solar in this step
        load_kwh : float
            Energy demanded by the house in this step
        
        Explanation:
        ------------
        This is the most important function. Here we decide:
        - Do we use solar for the house or for the battery first?
        - Do we import from the grid or use the battery?
        - Do we export the excess to the grid?
        """
        strategy = config.ENERGY_MANAGEMENT_STRATEGY
        
        if strategy == 'LOAD_PRIORITY':
            self._load_priority_strategy(solar_kwh, load_kwh)
        elif strategy == 'CHARGE_PRIORITY':
            self._charge_priority_strategy(solar_kwh, load_kwh)
        elif strategy == 'PRODUCE_PRIORITY':
            self._produce_priority_strategy(solar_kwh, load_kwh)
        else:
            # By default, use LOAD_PRIORITY
            self._load_priority_strategy(solar_kwh, load_kwh)
    
    def _load_priority_strategy(self, solar_kwh, load_kwh):
        """
        Strategy: House → Battery → Grid
        
        Priority:
        1. Satisfy house demand first
        2. Charge battery with excess
        3. Export to grid what's left over
        """
        remaining_solar = solar_kwh
        remaining_load = load_kwh
        
        # Step 1: Use solar to satisfy load
        solar_to_load = min(remaining_solar, remaining_load)
        remaining_solar -= solar_to_load
        remaining_load -= solar_to_load
        
        # Step 2: If there's still demand, use battery
        if remaining_load > 0:
            battery_to_load = self.battery.discharge(remaining_load, self.time_step_hours)
            remaining_load -= battery_to_load
        
        # Step 3: If there's still demand, import from grid
        if remaining_load > 0:
            grid_import = self.grid.import_energy(remaining_load)
            remaining_load -= grid_import
        
        # Record unmet load (shouldn't happen if grid is infinite)
        if remaining_load > 0:
            self.load.record_unmet_load(remaining_load)
        
        # Step 4: If there's excess solar, charge battery
        if remaining_solar > 0:
            charged = self.battery.charge(remaining_solar, self.time_step_hours)
            remaining_solar -= charged
        
        # Step 5: If there's still excess solar, export to grid
        if remaining_solar > 0:
            exported = self.grid.export_energy(remaining_solar)
            remaining_solar -= exported
        
        # Record consumption and generation
        self.load.consume(load_kwh - remaining_load)
        self.solar.total_generated += solar_kwh
    
    def _charge_priority_strategy(self, solar_kwh, load_kwh):
        """
        Strategy: Battery → House → Grid
        
        Priority:
        1. Charge battery first
        2. Satisfy house demand
        3. Export excess
        """
        remaining_solar = solar_kwh
        remaining_load = load_kwh
        
        # Step 1: Charge battery first
        charged = self.battery.charge(remaining_solar, self.time_step_hours)
        remaining_solar -= charged
        
        # Step 2: Use remaining solar for house
        solar_to_load = min(remaining_solar, remaining_load)
        remaining_solar -= solar_to_load
        remaining_load -= solar_to_load
        
        # Step 3: If there's still demand, use battery
        if remaining_load > 0:
            battery_to_load = self.battery.discharge(remaining_load, self.time_step_hours)
            remaining_load -= battery_to_load
        
        # Step 4: If there's still demand, import from grid
        if remaining_load > 0:
            grid_import = self.grid.import_energy(remaining_load)
            remaining_load -= grid_import
        
        # Step 5: Export excess
        if remaining_solar > 0:
            exported = self.grid.export_energy(remaining_solar)
        
        # Record
        self.load.consume(load_kwh - remaining_load)
        self.solar.total_generated += solar_kwh
        if remaining_load > 0:
            self.load.record_unmet_load(remaining_load)
    
    def _produce_priority_strategy(self, solar_kwh, load_kwh):
        """
        Strategy: Grid → Battery → House
        
        Priority:
        1. Export to grid first (up to limit)
        2. Charge battery
        3. Satisfy house demand
        """
        remaining_solar = solar_kwh
        remaining_load = load_kwh
        
        # Step 1: Export first
        exported = self.grid.export_energy(remaining_solar)
        remaining_solar -= exported
        
        # Step 2: Charge battery
        charged = self.battery.charge(remaining_solar, self.time_step_hours)
        remaining_solar -= charged
        
        # Step 3: Use solar for house
        solar_to_load = min(remaining_solar, remaining_load)
        remaining_load -= solar_to_load
        
        # Step 4: Use battery
        if remaining_load > 0:
            battery_to_load = self.battery.discharge(remaining_load, self.time_step_hours)
            remaining_load -= battery_to_load
        
        # Step 5: Import from grid if necessary
        if remaining_load > 0:
            grid_import = self.grid.import_energy(remaining_load)
            remaining_load -= grid_import
        
        # Record
        self.load.consume(load_kwh - remaining_load)
        self.solar.total_generated += solar_kwh
        if remaining_load > 0:
            self.load.record_unmet_load(remaining_load)
    
    def log_data(self, current_hour, hour_of_day, solar_kw, load_kw):
        """
        Records current state data for later analysis.
        """
        self.data_log.append({
            'timestamp_hours': current_hour,
            'day': self.current_day,
            'hour_of_day': hour_of_day,
            'solar_generation_kw': round(solar_kw, 3),
            'load_demand_kw': round(load_kw, 3),
            'battery_soc_percent': round(self.battery.current_soc, 2),
            'battery_energy_kwh': round(self.battery.get_current_energy(), 2),
            'grid_import_kwh': round(self.grid.total_imported, 2),
            'grid_export_kwh': round(self.grid.total_exported, 2),
            'cloud_coverage': round(self.daily_cloud_coverage, 2),
            'inverter_operational': self.inverter.is_operational
        })
    
    def print_status(self, hour, solar_kw, load_kw):
        """Prints the current simulation status."""
        time_str = utils.format_time(hour)
        print(f"\n{time_str}")
        print(f"  ☀️  Solar: {solar_kw:.2f} kW | 🏠 Load: {load_kw:.2f} kW")
        print(f"  🔋 Battery: {self.battery.current_soc:.1f}% ({self.battery.get_current_energy():.2f} kWh)")
        print(f"  ⚡ Inverter: {'✅ OK' if self.inverter.is_operational else '❌ FAILURE'}")
    
    def print_summary(self):
        """Prints a final simulation summary."""
        print("\n📊 SIMULATION SUMMARY")
        print("-" * 70)
        
        # Battery
        print("\n🔋 BATTERY:")
        bat_status = self.battery.get_status()
        print(f"  Quantity: {bat_status['battery_count']} unit(s)")
        print(f"  Total capacity: {bat_status['capacity_kwh']} kWh")
        print(f"  Final SOC: {bat_status['soc_percent']}%")
        print(f"  Total Charged: {bat_status['total_charged']:.2f} kWh")
        print(f"  Total Discharged: {bat_status['total_discharged']:.2f} kWh")
        print(f"  Charge Cycles: {self.battery.charge_cycles}")
        
        # Solar
        print("\n☀️ SOLAR GENERATION:")
        solar_status = self.solar.get_status()
        print(f"  Total Generated: {solar_status['total_generated_kwh']:.2f} kWh")
        print(f"  Total Wasted (clipping): {solar_status['total_clipped_kwh']:.2f} kWh")
        
        # Load
        print("\n🏠 CONSUMPTION:")
        load_status = self.load.get_status()
        print(f"  Total Consumed: {load_status['total_consumed_kwh']:.2f} kWh")
        print(f"  Peak Demand: {load_status['peak_demand_kw']:.2f} kW")
        print(f"  Unmet Load Events: {load_status['unmet_load_events']}")
        
        # Grid
        print("\n🔌 ELECTRIC GRID:")
        grid_status = self.grid.get_status()
        print(f"  Total Imported: {grid_status['total_imported_kwh']:.2f} kWh")
        print(f"  Total Exported: {grid_status['total_exported_kwh']:.2f} kWh")
        print(f"  Total Cost: ${grid_status['total_cost_cents']:.2f}")
        print(f"  Total Revenue: ${grid_status['total_revenue_cents']:.2f}")
        print(f"  Net Balance: ${grid_status['net_cost_cents']:.2f}")
        
        # Inverter
        print("\n⚡ INVERTER:")
        inv_status = self.inverter.get_status()
        print(f"  Total Failures: {inv_status['total_failures']}")
        print(f"  Total Downtime: {inv_status['total_downtime_hours']:.1f} hours")
        
        print("\n" + "=" * 70)
    
    def export_data(self):
        """Exports recorded data to a CSV file."""
        df = pd.DataFrame(self.data_log)
        filename = config.OUTPUT_FILE
        df.to_csv(filename, index=False)
        print(f"\n💾 Data exported to: {filename}")
        print(f"   Total records: {len(df)}")