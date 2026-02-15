import random
import config


class Inverter:
    def __init__(self, max_output:float=config.INVERTER_MAX_OUTPUT, fail_rate:float=config.INVERTER_FAILURE_RATE, min_fail_duration:float=config.INVERTER_MIN_FAILURE_HOURS, max_fail_duration: float=config.INVERTER_MAX_FAILURE_HOURS):
        self.__max_output = max_output                  # Max Output (kW)
        self.__fail_rate = fail_rate                    # Probability of the inverter to fail. (0-1)
        self.__min_fail_duration = min_fail_duration    # Min duration of downtime
        self.__max_fail_duration = max_fail_duration    # Max duration of downtime
        self.__is_operational = True    
        self.__failure_time_remaining = 0
        self.__total_failures = 0      
        self.__total_downtime_hours = 0

    def __inverter_fails(self) -> tuple[bool, int]:
        """Checks if the inverter fails.

        Returns:
            tuple[bool, int]: Tuple containing whether the inverter fails and the downtime it will have.
        """
        # Checks if the inverter fails
        fails = random.random() < self.__fail_rate

        # Calculates the downtime
        duration = random.randint(self.__min_fail_duration, self.__max_fail_duration)

        return fails, duration if fails else 0
        
    def __update_failure(self, duration_hours:int):
        """Updates the fail status of the inverter, whether from failing or resuming from a failure.

        Args:
            duration_hours (int): The amount of downtime the inverter will have.
        """
        self.__is_operational = not self.__is_operational
        self.__failure_time_remaining = duration_hours
        self.__total_downtime_hours += duration_hours
        if not self.__is_operational: self.__total_failures += 1 
        
        if config.VERBOSE:
            if self.__is_operational: print(f"  ⚡ Inverter working again")
            else: print(f"  ❌ ¡INVERTER FAILURE! Downtime: {duration_hours} hours")
    
    def update(self, time_step_hours:float):
        """Updates the status of the inverter, may cause failure depending on the hours used.

        Args:
            time_step_hours (float): The amount of hours the inverter is used.
        """
        if not self.__is_operational:
            self.__failure_time_remaining -= time_step_hours
            if self.__failure_time_remaining <= 0: self.__update_failure(0)
        else:
            step_failure_prob = self.__fail_rate * (time_step_hours / 24.0)
            
            if random.random() < step_failure_prob:
                failed, duration = self.__inverter_fails()
                if failed: self.__update_failure(duration)
    
    def get_max_output(self) -> float:
        return self.__max_output
    
    def is_operational(self) -> bool:
        return self.__is_operational
    
    def get_status(self):
        return {
            'is_operational': self.__is_operational,
            'max_output_kw': self.__max_output,
            'failure_time_remaining': round(self.__failure_time_remaining, 2),
            'total_failures': self.__total_failures,
            'total_downtime_hours': round(self.__total_downtime_hours, 2)
        }
