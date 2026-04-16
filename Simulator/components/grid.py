"""
Grid Component
 handles both importing (buying) and exporting (selling) energy.
"""

class Grid:
    def __init__(self, cfg: dict):
        # Initialize main parameters from the config 
        self.export_limit    = cfg["export_limit_kw"]           # max energy that can be exported
        self.import_cost     = cfg["import_cost_per_kwh"]       # cost per kWh when importing
        self.export_revenue  = cfg["export_revenue_per_kwh"]    # revenue per kWh when exporting

        # Variables 
        self.total_imported  = 0.0  # total energy imported
        self.total_exported  = 0.0  # total energy exported
        self.total_cost      = 0.0  # total cost of imported energy
        self.total_revenue   = 0.0  # total revenue from exported energy

    def import_energy(self, kwh: float) -> float:
        # method to import energy from the grid
        if kwh <= 0:
            return 0.0  # ignore invalid values

        # Update total imported energy and cost
        self.total_imported += kwh
        self.total_cost     += kwh * self.import_cost

        return kwh  # imported amount

    def export_energy(self, kwh: float) -> float:
        # method to export energy to the grid
        if kwh <= 0:
            return 0.0  # ignore invalid values

        # Make sure we don't exceed the export limit
        actual = min(kwh, self.export_limit)

        # Update total exported energy and revenue
        self.total_exported += actual
        self.total_revenue  += actual * self.export_revenue

        return actual  # return actual exported amount

    def get_net_cost(self) -> float:
        # Net cost = total cost - total revenue
        return self.total_cost - self.total_revenue

    def get_status(self) -> dict:
        # Returns a summary of the current state
        return {
            "total_imported_kwh":  round(self.total_imported,  2),  # total imported energy
            "total_exported_kwh":  round(self.total_exported,  2),  # total exported energy
            "total_cost":          round(self.total_cost,       2), # total cost
            "total_revenue":       round(self.total_revenue,    2), # total revenue
            "net_cost":            round(self.get_net_cost(),   2), # final net cost
        }