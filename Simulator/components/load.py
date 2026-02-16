"""
Load component = electricity consumption of the house.
"""

import config
import utils


class Load:
    
    def __init__(self):
        
        self.base_load = config.BASE_LOAD  
        
        # Stats
        self.total_consumed = 0.0   
        self.peak_demand = 0.0      
        self.unmet_load_events = 0  
        self.total_unmet_load = 0.0  
    
    def get_demand(self, hour_of_day):
        """
        Calculate the energy demand at this moment

        Parameters:
            hour_of_day: int
            Time of day (0-23)

        Returns:
            float: Energy demand in kW

        The demand is the sum of:
            1. Base load (devices always on)
            2. Random peaks (especially during peak hours)
            3. Small random variability
        """
        demand = utils.calculate_load_demand(hour_of_day)
        
        
        if demand > self.peak_demand:
            self.peak_demand = demand
        
        return demand
    
    def consume(self, energy_kwh):
        """
        Energy consumption

        Parameters:
            energy_kwh : float
            Energy consumed in this step (kWh)
        """
        self.total_consumed += energy_kwh
    
    def record_unmet_load(self, unmet_kwh):
        """
        Record when the total demand could not be met

        Parameters:
            unmet_kwh: float
            Energy needed but could not be supplied (kWh)
        """
        if unmet_kwh > 0:
            self.unmet_load_events += 1
            self.total_unmet_load += unmet_kwh
            
            if config.VERBOSE:
                print(f"Unmet charge: {unmet_kwh:.2f} kWh")
    
    def get_status(self):
        """
        Current state of load
        """
        return {
            'base_load_kw': self.base_load,
            'peak_demand_kw': round(self.peak_demand, 2),
            'total_consumed_kwh': round(self.total_consumed, 2),
            'unmet_load_events': self.unmet_load_events,
            'total_unmet_load_kwh': round(self.total_unmet_load, 2)
        }
