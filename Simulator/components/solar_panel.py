import math


class SolarPanel:
    def __init__(self, cfg: dict):
        self.peak_power = cfg["peak_power_kw"]
        self.total_generated = 0.0
        self.total_clipped   = 0.0

    def generate(self, hour_of_day: int, cloud_coverage: float, 
                 inverter_operational: bool, inverter_max_kw: float) -> float:
        """
        Generates energy depending on the hour of day and cloud coverage, 
        generates 0 energy when the inverter is not working 

        Args:
            hour_of_day (int): The hour of day when energy is going to be generated
            cloud_coverage (float): The percentage of cloud coverage
            inverter_operational (bool): Whether the inverter is working or not
            inverter_max_kw (float): The max amount of energy generated

        Returns:
            float: The amount of energy generated
        """
        if not inverter_operational:
            return 0.0

        sun_angle = hour_of_day * (math.pi / 12)
        raw_generation = max(self.peak_power * math.sin(sun_angle), 0.0)
        after_clouds = raw_generation * (1 - cloud_coverage)

        clipped = max(after_clouds - inverter_max_kw, 0.0)
        output  = after_clouds - clipped

        self.total_clipped += clipped
        self.total_generated += output
        return output

    def get_status(self) -> dict:
        return {
                "peak_power_kw": self.peak_power,
                "total_generated_kwh": round(self.total_generated, 2),
                "total_clipped_kwh": round(self.total_clipped, 2),
               }