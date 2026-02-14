"""
Auxiliar Functions

This file contains utility functions used troughout the simulator.
"""

import random
import math
import config


def calculate_solar_generation(time_of_day, cloud_coverage):
    """
    Calculate the solar generation based on the time of day and clouds couverage 
    
    Explanation:
    ------------
   Use a sinusoidal function to simulate that the sun generates more energy
   at noon (12:00) and none during the night.
    """
    # Using the time of day callculates the sun angle
    sun_angle = time_of_day * (math.pi / 12)
    
    # Based on the sun angle calcukates the generation
    base_generation = config.SOLAR_PEAK_POWER * math.sin(sun_angle)
    
    # Avoid negative values in the generation
    if base_generation < 0:
        base_generation = 0.0
    
    # Reduce by clouds couverage
    generation_with_clouds = base_generation * (1 - cloud_coverage)
    
    return max(0, generation_with_clouds)  # Cant be negative


def get_daily_cloud_coverage(season):
    """
    Generates a clouds couverage level for the day based on the season
    
    """
    # Get season's cloud probabilities
    probabilities = config.CLOUD_COVERAGE_PROBABILITIES.get(season, (0.25, 0.25, 0.25, 0.25))
    
    # Select type of day based on probabilities
    cloud_types = ['clear', 'partly_cloudy', 'mostly_cloudy', 'overcast']
    selected_type = random.choices(cloud_types, weights=probabilities)[0]
    
    # Get the range for the type of day
    min_coverage, max_coverage = config.CLOUD_RANGES[selected_type]
    
    # Get a random value within the range
    cloud_coverage = random.uniform(min_coverage, max_coverage)
    
    return cloud_coverage


def calculate_load_demand(time_of_day):
    """
    Calculates the house's energy demand, based on the time of day,
    
    Explanation:
    ------------

    Combines the base load (appliances always on) with random peak loads
    during peak hours (evening/night)

    """
    # Carga base (nevera, router, luces básicas)
    load = config.BASE_LOAD
    
    # Agregar variabilidad aleatoria pequeña
    load += random.uniform(0, config.BASE_LOAD * config.LOAD_VARIABILITY)
    
    # Picos durante horas de consumo alto (6 PM - 9 PM)
    if config.PEAK_HOURS_START <= time_of_day <= config.PEAK_HOURS_END:
        # Durante horas pico, agregar carga adicional aleatoria
        peak_load = random.uniform(0, config.PEAK_LOAD_MAX)
        load += peak_load
    
    return load


def check_inverter_failure():
    """
    Determines if the inverter fails at this moment
    
    """
    # Failure probabilities
    if random.random() < config.INVERTER_FAILURE_RATE:

        # Random failure duration
        duration = random.randint(
            config.INVERTER_MIN_FAILURE_HOURS,
            config.INVERTER_MAX_FAILURE_HOURS
        )
        return True, duration
    
    return False, 0


def format_time(hours):
    """
    Convert simulation hours to a readable format.
    
    """
    day = int(hours // 24) + 1
    hour = int(hours % 24)
    minute = int((hours % 1) * 60)
    
    return f"Day {day}, {hour:02d}:{minute:02d}"


def clamp(value, min_value, max_value):
    """
    Limits a value between a minimum and a maximum.

    Useful for ensuring that values ​​such as the charge level 
    do not exceed acceptable ranges.
    """
    return max(min_value, min(value, max_value))