import random
import simpy

class Inverter:
    def __init__(self, cfg: dict, env: simpy.Environment):
        self.env = env
        self.max_output = cfg["max_output_kw"]
        self.failure_rate = cfg["failure_rate_per_day"]
        self.min_fail_hours = cfg["min_failure_hours"]
        self.max_fail_hours = cfg["max_failure_hours"]

        self._operational = True
        self.total_failures = 0
        self.total_downtime_hours = 0.0

        self.env.process(self._failure_monitor())

    def _failure_monitor(self):
        """
        Checks every hour for inverter failure
        """
        while True:
            yield self.env.timeout(1)
            if self._operational:
                hourly_failure_rate = self.failure_rate / 24.0
                if random.random() < (hourly_failure_rate):
                    duration = random.uniform(self.min_fail_hours, self.max_fail_hours)
                    self.env.process(self._handle_failure(duration))

    def _handle_failure(self, duration_hours: float):
        """
        Updates information regarding failure
        """
        self._operational          = False
        self.total_failures        += 1
        self.total_downtime_hours  += duration_hours
        yield self.env.timeout(duration_hours)
        self._operational = True

    def is_operational(self) -> bool:
        return self._operational

    def get_status(self) -> dict:
        return {
                "is_operational": self._operational,
                "max_output_kw": self.max_output,
                "total_failures": self.total_failures,
                "total_downtime_hours": round(self.total_downtime_hours, 2),
               }