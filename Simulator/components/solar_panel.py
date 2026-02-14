import config
import math

class SolarPanel:
    
    def __init__(self, peak_power: float=config.SOLAR_PEAK_POWER):
        self.__peak_power = peak_power      # Max energy generated (kW)
        self.__total_generated = 0.0        # Total energy generated (kW)
        self.__total_clipped = 0.0          # Total energy lost by inverter limit (kW)
    
    def __generate(self, hour_of_day: int, cloud_coverage: float) -> float:
        """Calculates energy produced depending on the hour of day and cloud coverage.

        Args:
            hour_of_day (int): The hour of the day when the panel is producing energy. (0-23)
            cloud_coverage (float): The percentage of sky covered by clouds. (0-1)

        Returns:
            float: The amount of energy produced by the solar panel.
        """
        # Using the time of day to calculate the sun angle
        sun_angle = hour_of_day * (math.pi / 12)

        # Calculates generation depending on the sun angle, using sine function
        base_generation = max(self.__peak_power * math.sin(sun_angle), 0.0)
    
        # Adjust production with cloud coverage
        return base_generation * (1 - cloud_coverage)

    def generate_energy(self, hour_of_day: int, cloud_coverage: float, inverter_operational: bool, limit:float) -> float:
        """Calculates the solar generation of the panel, limited by the inverter.

        Args:
            hour_of_day (int): The hour of the day when the panel is producing energy. (0-23)
            cloud_coverage (float): The percentage of sky covered by clouds. (0-1)
            inverter_operational (bool): Whether the inverter is working or not.
            limit (float, optional): The inverter output limit.

        Returns:
            float: The amount of energy produced by the solar panel and limited by the inverter.
        """
        if not inverter_operational: return 0.0

        energy = self.__generate(hour_of_day, cloud_coverage)
        self.__total_clipped += max(energy - limit, 0.0)
        self.__total_generated += min(energy, limit)

        return min(energy, limit)
    
    def get_status(self):
        return {
            'peak_power_kw': self.__peak_power,
            'total_generated_kw': round(self.__total_generated, 2),
            'total_clipped_kw': round(self.__total_clipped, 2)
        }