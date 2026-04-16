"""
GreenGrid Simulator — Entry Point
Usage:
    python main.py                        # uses default config.json
    python main.py --config config.json   # explicit config
    python main.py --days 7 --verbose     # override params inline
"""

import sys
import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def check_dependencies() -> bool:
    required = {"simpy": "SimPy", "pandas": "Pandas", "numpy": "NumPy"}
    missing  = [f"  pip install {pkg}  # {desc}"
                for pkg, desc in required.items()
                if not _can_import(pkg)]
    if missing:
        print("❌ Missing dependencies:\n" + "\n".join(missing))
        print("\nOr just run:  pip install -r requirements.txt")
        return False
    return True


def _can_import(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="GreenGrid Neighborhood Simulator")
    parser.add_argument("--config",  default=str(BASE_DIR / "config.json"),
                        help="Path to JSON config file")
    parser.add_argument("--days",    type=int,   default=None, help="Override simulation days")
    parser.add_argument("--season",  default=None,
                        choices=["spring", "summer", "fall", "winter"],
                        help="Override season")
    parser.add_argument("--strategy", default=None,
                        choices=["LOAD_PRIORITY", "CHARGE_PRIORITY", "PRODUCE_PRIORITY"],
                        help="Override energy management strategy")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if not check_dependencies():
        sys.exit(1)

    # ── Lazy imports after dependency check ──────────────────────────── #
    from simulation     import NeighborhoodSim
    from data_preparation import prepare

    # ── Load config ───────────────────────────────────────────────────── #
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"❌ Config file not found: {cfg_path}")
        sys.exit(1)

    cfg = load_config(cfg_path)

    # ── CLI overrides ─────────────────────────────────────────────────── #
    if args.days:    cfg["simulation"]["days"]                           = args.days
    if args.season:  cfg["simulation"]["season"]                         = args.season
    if args.strategy: cfg["simulation"]["energy_management_strategy"]    = args.strategy
    if args.verbose: cfg["simulation"]["verbose"]                        = True

    # ── Output directory ──────────────────────────────────────────────── #
    out_cfg    = cfg.get("output", {})
    output_dir = BASE_DIR.parent / out_cfg.get("directory", "data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Run simulation ────────────────────────────────────────────────── #
    print("=" * 65)
    print("🌞  GREENGRID NEIGHBORHOOD SIMULATOR")
    print("=" * 65)
    sim_cfg = cfg["simulation"]
    print(f"   Season   : {sim_cfg['season'].capitalize()}")
    print(f"   Days     : {sim_cfg['days']}")
    print(f"   Strategy : {sim_cfg['energy_management_strategy']}")
    print(f"   Households: {len(cfg['households'])}")
    print(f"   Time step: {sim_cfg['time_step_minutes']} min")
    print("=" * 65)

    sim = NeighborhoodSim(cfg)
    neighborhood_log = sim.run()
    household_log    = sim.get_all_household_logs()
    summaries        = sim.get_summaries()

    print(f"\n✅ Simulation done — {len(household_log)} household records")

    # ── Data preparation ──────────────────────────────────────────────── #
    print("\n📊 Preparing data for dashboard...")
    produced = prepare(household_log, neighborhood_log, summaries, output_dir)

    print(f"\n💾 Files written to: {output_dir}")
    for key, path in produced.items():
        print(f"   {key:<30} → {Path(path).name}")

    print("\n✨ Done! Open Dashboard/index.html in your browser.")
    print(f"   Data directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()