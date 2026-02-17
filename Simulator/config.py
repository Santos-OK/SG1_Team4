"""
Green Grid Simulator's configuration File 

This file contains all the configurable parameters for the simulator.

"""

# ============================================================================
# BATTERY SETTINGS
# ============================================================================
BATTERY_COUNT = 1        # Number of batteries
BATTERY_CAPACITY = 13.5  # Battery´s capacity (KWh)
BATTERY_MIN_SOC = 5      # Minimum State of Charge Allowed (%)
BATTERY_MAX_SOC = 100    # Maximum State of Charge (%)
BATTERY_EFFICIENCY = 0.9 # Charge/Discharge Efficiency (90%)
BATTERY_INITIAL_SOC = 50 # Initial State of Charge (%)

# ============================================================================
# SOLAR PANELS SETTINGS
# ============================================================================
SOLAR_PEAK_POWER = 5.0   # Maximum Generation Capacity (KWh)

# ============================================================================
# INVERTER SETTINGS
# ============================================================================
INVERTER_MAX_OUTPUT = 4.0       # Maximum Inverter Output (kW)
INVERTER_FAILURE_RATE = 0.005   # Failure Probability (0.5%)
INVERTER_MIN_FAILURE_HOURS = 4  # Minimum Failure Duration (hours)
INVERTER_MAX_FAILURE_HOURS = 72 # Maximum Failure Duration (hours)

# ============================================================================
# LOAD SETTINGS 
# ============================================================================
BASE_LOAD = 0.5          # Constant Base Load (KWh)
PEAK_LOAD_MAX = 3.0      # Maximum Load Peak (KWh)
PEAK_HOURS_START = 18    # Peak Consume Start Hour (6 PM)
PEAK_HOURS_END = 21      # Peak Consume End Hour (9 PM)
LOAD_VARIABILITY = 0.3   # Random Variability Factor

# ============================================================================
# ELECTRIC GRID SETTINGS
# ============================================================================
GRID_EXPORT_LIMIT = 20.0     # Maximum Export Limit to the Grid (kW)
GRID_IMPORT_COST = 0.75      # Energy Import Cost (cents/kWh)
GRID_EXPORT_REVENUE = 0.90   # Energy Export Revenue (cents/kWh)

# ============================================================================
# Energetic Management Strategy
# ============================================================================
# Options: 'LOAD_PRIORITY', 'CHARGE_PRIORITY', 'PRODUCE_PRIORITY'
ENERGY_MANAGEMENT_STRATEGY = 'CHARGE_PRIORITY'

# LOAD_PRIORITY: House First → Battery → Grid
# CHARGE_PRIORITY: Battery first → House → Grid  
# PRODUCE_PRIORITY: Grid First → Battery → House

# ============================================================================
# CONFIGURACIÓN DE COBERTURA DE NUBES (Por Estación)
# ============================================================================
# Each station has probabilities for: (Clear, Partly Cloudy, Mostly Cloudy, Overcast)

CLOUD_COVERAGE_PROBABILITIES = {
    'spring': (0.1, 0.3, 0.4, 0.2),   # Spring
    'summer': (0.05, 0.15, 0.3, 0.5), # Summer
    'fall': (0.2, 0.4, 0.3, 0.1),     # Autumn
    'winter': (0.3, 0.4, 0.2, 0.1)    # Winter  
}

# Cloud couverage range (reduce the solar generation)
CLOUD_RANGES = {
    'clear': (0.0, 0.2),           # Clear: 0-20% cloudy
    'partly_cloudy': (0.2, 0.6),   # Partly cloudy: 20-60%
    'mostly_cloudy': (0.6, 0.8),   # Mostly cloudy: 60-80%
    'overcast': (0.8, 0.9)         # Overcast: 80-90%
}

# ============================================================================
# SIMULATION SETTIGNS
# ============================================================================
SIMULATION_DAYS = 30         # Number of day to simulate
TIME_STEP_MINUTES = 60       # Time in minutes Interval (60 = 1 hour)
SEASON = 'spring'            # Season: 'spring', 'summer', 'fall', 'winter'

# ============================================================================
# LOGGING & OUTPUT SETTINGS
# ============================================================================
LOG_INTERVAL_HOURS = 1       # How often to save data
OUTPUT_FILE = 'test.csv'  # Output File
VERBOSE = True             # Show messages in Console During the Simulation