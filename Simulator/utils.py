"""
Utility Functions for GreenGrid Simulator.
"""

import random


def get_daily_cloud_coverage(season: str, cfg: dict) -> float:
    """Returns a random cloud coverage value for the day based on season probabilities."""
    probs      = cfg["probabilities"][season]
    cloud_types = ["clear", "partly_cloudy", "mostly_cloudy", "overcast"]
    selected   = random.choices(cloud_types, weights=probs)[0]
    lo, hi     = cfg["ranges"][selected]
    return random.uniform(lo, hi)


def format_time(hours: float) -> str:
    day  = int(hours // 24) + 1
    hour = int(hours % 24)
    mins = int((hours % 1) * 60)
    return f"Day {day:>3}, {hour:02d}:{mins:02d}"


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))