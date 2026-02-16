"""
Battery Component

The battery stores energy for use when there is no sun.
"""

import config


class Battery:
    """
   Class representing the system's battery.

    What does a battery do?

    ----------------------

    - ​​Stores energy when there is excess solar generation
    - Supplies energy when there is demand but no sun
    - Has capacity limits (it cannot store infinite energy)
    - Loses efficiency when charging/discharging (it is not 100% efficient)
    """
    
    def __init__(self, count=1):
        """
        Constructor: Initialize battery with config.py values
        """
        self.count = count
        self.capacity = config.BATTERY_CAPACITY * count  # Total Capacity (KWh)
        self.min_soc = config.BATTERY_MIN_SOC    # Minimum State of Charge (%)
        self.max_soc = config.BATTERY_MAX_SOC    # Maximum State of Charge (%)
        self.efficiency = config.BATTERY_EFFICIENCY  # Efficiency (0.9 = 90%)
        
        # Estado actual: empieza al 50%
        self.current_soc = config.BATTERY_INITIAL_SOC  # State of Charge (%)
        
        # Estadísticas
        self.total_charged = 0.0    # Total de energía cargada (kWh)
        self.total_discharged = 0.0  # Total de energía descargada (kWh)
        self.charge_cycles = 0       # Número de veces que se cargó
        self.discharge_cycles = 0    # Número de veces que se descargó
    
    def get_current_energy(self):
        """
        Returns current energy stored (KWh)
        
        """
        return (self.current_soc / 100.0) * self.capacity
    
    def charge(self, energy_kwh, time_step_hours=1.0):
        """
        Try to charge the battery with a certain amount of energy
        
        Parameters:
        -----------
        energy_kwh : float
            Amount of energy available to charge (kWh)
        time_step_hours : float
            Duration of time step (hours) - for compatibility with simulation
        
        Explanation:
        ------------
        1. Apply efficiency loss (only 90% of incoming data is stored)
        2. Verify that the maximum capacity is not exceeded
        3. Update the load status
        """
        # Apply efficiency: if 1 kWh enters, only 0.9 kWh is stored
        effective_energy = energy_kwh * self.efficiency
        
        # Calculate how much energy we can store without exceeding the maximum
        current_energy = self.get_current_energy()
        max_energy = (self.max_soc / 100.0) * self.capacity
        available_space = max_energy - current_energy
        
        # Choose the minimum between what you want to load and the available space.
        actual_charged = min(effective_energy, available_space)
        
        # Update state of charge
        if actual_charged > 0:
            new_energy = current_energy + actual_charged
            self.current_soc = (new_energy / self.capacity) * 100.0
            self.total_charged += actual_charged
            self.charge_cycles += 1
        
        return actual_charged
    
    def discharge(self, energy_needed_kwh, time_step_hours=1.0):
        """
        Try drawing power from the battery.
        
        Parameters:
        -----------
        energy_needed_kwh : float
            Amount of energy needed (kWh)
        time_step_hours : float
            Duration of time step (hours) - for compatibility with simulation
        
        Explanation:
        ------------
        1. Verify that the discharge level does not fall below the minimum (5%).
        2. Apply efficiency loss.
        3. Update the charge status.

        """

        # Calculate how much energy we can extract without going below the minimum.
        current_energy = self.get_current_energy()
        min_energy = (self.min_soc / 100.0) * self.capacity
        available_energy = current_energy - min_energy
        
        # We can't get more than what's available.
        actual_discharge = min(energy_needed_kwh, available_energy)
        
        # Apply loss due to inefficiency when downloading
        effective_discharge = actual_discharge * self.efficiency
        
        # Update state of charge
        if actual_discharge > 0:
            new_energy = current_energy - actual_discharge
            self.current_soc = (new_energy / self.capacity) * 100.0
            self.total_discharged += effective_discharge
            self.discharge_cycles += 1
        
        return effective_discharge
    
    def is_full(self):
        """Check if the battery is fully charged."""
        return self.current_soc >= self.max_soc
    
    def is_empty(self):
        """Check if the battery is empty (at the minimum allowed)."""
        return self.current_soc <= self.min_soc
    
    def get_status(self):
        """
        Returns a dictionary containing the current battery status.
        Useful for logging and analysis.
        """
        return {
            'battery_count': self.count,
            'soc_percent': round(self.current_soc, 2),
            'energy_kwh': round(self.get_current_energy(), 2),
            'capacity_kwh': self.capacity,
            'is_full': self.is_full(),
            'is_empty': self.is_empty(),
            'total_charged': round(self.total_charged, 2),
            'total_discharged': round(self.total_discharged, 2)
        }