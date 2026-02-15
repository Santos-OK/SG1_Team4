"""
grid.py - Electrical Grid Component

"""

import config


class Grid:
    """
    
    Electrical grid?
    -----------------
    Supplies energy when we don't have enough (imports)
    Receives energy when we have a surplus (exports)
    Has limits on how much we can export
    Records costs and revenues
    """
    
    def __init__(self):
     
        self.export_limit = config.GRID_EXPORT_LIMIT  
        self.import_cost = config.GRID_IMPORT_COST    
        self.export_revenue = config.GRID_EXPORT_REVENUE  
        
        # Stats
        self.total_imported = 0.0   
        self.total_exported = 0.0   
        self.total_cost = 0.0       
        self.total_revenue = 0.0   
    
    def import_energy(self, energy_kwh):
        """
       Import energy from the grid (we buy electricity).

        Parameters:
            energy_kwh: float
            Amount of energy to import (kWh)

        Returns:
            float: Energy actually imported

        Explanation:
            The grid can always supply energy (it is "infinite").
            We calculate the cost and record it.
        """
        if energy_kwh <= 0:
            return 0.0
        
        self.total_imported += energy_kwh

        cost = energy_kwh * self.import_cost
        self.total_cost += cost
        
        return energy_kwh
    
    def export_energy(self, energy_kwh):
        """
        Exports energy to the grid (we sell electricity).

        Parameters:
            energy_kwh: float
            Amount of energy to export (kWh)

        Returns:
            float: Energy actually exported (may be less due to a limit)

        Explanation:
            The grid has a limit on how much we can export.
            If we try to export more, the excess is lost.
        """
        if energy_kwh <= 0:
            return 0.0
        
      
        actual_export = min(energy_kwh, self.export_limit)
        
        self.total_exported += actual_export
        
        revenue = actual_export * self.export_revenue
        self.total_revenue += revenue
        
        curtailed = energy_kwh - actual_export
        if curtailed > 0 and config.VERBOSE:
            print(f" wasted energy (curtailment): {curtailed:.2f} kWh")
        
        return actual_export
    
    def get_net_cost(self):
        """
       Calculate the net cost (cost - profit).

        Returns:
            float: Net cost in $

        Explanation:
            If we spend $100 importing and earn $50 exporting,
            the net cost is $50.
            A negative value means we earned more than we spent

""
        """
        return self.total_cost - self.total_revenue
    
    def get_status(self):
        """
        Returns the current state of the network connection
        """
        return {
            'export_limit_kw': self.export_limit,
            'total_imported_kwh': round(self.total_imported, 2),
            'total_exported_kwh': round(self.total_exported, 2),
            'total_cost_cents': round(self.total_cost, 2),
            'total_revenue_cents': round(self.total_revenue, 2),
            'net_cost_cents': round(self.get_net_cost(), 2)
        }
