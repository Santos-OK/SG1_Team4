"""
Data Preparation Module
Automatically processes raw simulation output into structured datasets
ready for D3.js dashboard consumption.
No manual file movement required — paths are resolved relative to this file.
"""

import json
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent


# ═══════════════════════════════════════════════════════════════════════════ #
def prepare(household_log: list[dict],
            neighborhood_log: list[dict],
            summaries: list[dict],
            output_dir: Path) -> dict:
    """
    Master entry point.
    Transforms raw logs → dashboard-ready JSON files.
    Returns a dict with paths to every produced file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    produced = {}

    produced["duck_curve"]          = _duck_curve(neighborhood_log,  output_dir)
    produced["daily_totals"]        = _daily_totals(household_log,    output_dir)
    produced["hourly_heatmap"]      = _hourly_heatmap(household_log,  output_dir)
    produced["by_type"]             = _by_type(household_log,         output_dir)
    produced["by_wealth"]           = _by_wealth(household_log,       output_dir)
    produced["battery_soc"]         = _battery_soc(household_log,     output_dir)
    produced["grid_flow"]           = _grid_flow(neighborhood_log,    output_dir)
    produced["household_summaries"] = _summaries(summaries,           output_dir)
    produced["strategy_comparison"] = _strategy_comparison(summaries, output_dir)
    produced["neighborhood_series"] = _neighborhood_series(neighborhood_log, output_dir)

    # Write an index manifest so the dashboard knows what exists
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps({k: str(v) for k, v in produced.items()}, indent=2))

    return produced


# ─────────────────────────────────────────────────────────────────────────── #
def _write(data, path: Path) -> Path:
    path.write_text(json.dumps(data, indent=2))
    return path


# ── 1. Duck Curve ─────────────────────────────────────────────────────────── #
def _duck_curve(neighborhood_log: list[dict], out: Path) -> Path:
    """
    Average net load (load - solar) by hour-of-day across all days.
    Produces the classic duck curve shape.
    """
    buckets = defaultdict(list)
    for row in neighborhood_log:
        buckets[row["hour_of_day"]].append({
            "total_load":  row["total_load_kw"],
            "total_solar": row["total_solar_kw"],
            "net_load":    row["net_load_kw"],
        })

    curve = []
    for h in range(24):
        vals = buckets[h]
        if not vals:
            continue
        curve.append({
            "hour":        h,
            "avg_load_kw":  round(sum(v["total_load"]  for v in vals) / len(vals), 3),
            "avg_solar_kw": round(sum(v["total_solar"] for v in vals) / len(vals), 3),
            "avg_net_kw":   round(sum(v["net_load"]    for v in vals) / len(vals), 3),
        })

    return _write(curve, out / "duck_curve.json")


# ── 2. Daily totals per household ─────────────────────────────────────────── #
def _daily_totals(household_log: list[dict], out: Path) -> Path:
    """
    Per-household daily aggregates: solar_kwh, load_kwh, import, export, net_cost.
    Useful for time-series bar / line charts filtered by household.
    """
    key_fn  = lambda r: (r["household_id"], r["day"])
    buckets = defaultdict(list)
    for row in household_log:
        buckets[key_fn(row)].append(row)

    records = []
    for (hid, day), rows in sorted(buckets.items()):
        records.append({
            "household_id":   hid,
            "household_type": rows[0]["household_type"],
            "wealth":         rows[0]["wealth"],
            "day":            day,
            "solar_kwh":      round(sum(r["solar_kwh"]       for r in rows), 2),
            "load_kwh":       round(sum(r["load_kwh"]        for r in rows), 2),
            "import_kwh":     round(sum(r["grid_import_kwh"] for r in rows), 2),
            "export_kwh":     round(sum(r["grid_export_kwh"] for r in rows), 2),
            "self_consumed_kwh": round(
                sum(r["solar_kwh"] for r in rows) -
                sum(r["grid_export_kwh"] for r in rows), 2),
        })

    return _write(records, out / "daily_totals.json")


# ── 3. Hourly heatmap (avg load by hour × household type) ─────────────────── #
def _hourly_heatmap(household_log: list[dict], out: Path) -> Path:
    buckets = defaultdict(list)
    for row in household_log:
        buckets[(row["household_type"], row["hour_of_day"])].append(row["load_kw"])

    records = [
        {
            "household_type": htype,
            "hour":           hour,
            "avg_load_kw":    round(sum(vals) / len(vals), 3),
        }
        for (htype, hour), vals in sorted(buckets.items())
    ]
    return _write(records, out / "hourly_heatmap.json")


# ── 4. Totals by household type ───────────────────────────────────────────── #
def _by_type(household_log: list[dict], out: Path) -> Path:
    buckets = defaultdict(list)
    for row in household_log:
        buckets[row["household_type"]].append(row)

    records = []
    for htype, rows in sorted(buckets.items()):
        records.append({
            "household_type":   htype,
            "total_solar_kwh":  round(sum(r["solar_kwh"]       for r in rows), 2),
            "total_load_kwh":   round(sum(r["load_kwh"]        for r in rows), 2),
            "total_import_kwh": round(sum(r["grid_import_kwh"] for r in rows), 2),
            "total_export_kwh": round(sum(r["grid_export_kwh"] for r in rows), 2),
            "avg_load_kw":      round(sum(r["load_kw"]         for r in rows) / len(rows), 3),
            "self_sufficiency_pct": _self_suf(rows),
        })
    return _write(records, out / "by_type.json")


# ── 5. Totals by wealth level ─────────────────────────────────────────────── #
def _by_wealth(household_log: list[dict], out: Path) -> Path:
    order   = {"low": 0, "middle": 1, "high": 2, "luxury": 3}
    buckets = defaultdict(list)
    for row in household_log:
        buckets[row["wealth"]].append(row)

    records = []
    for wealth in sorted(buckets, key=lambda w: order.get(w, 99)):
        rows = buckets[wealth]
        records.append({
            "wealth":           wealth,
            "total_solar_kwh":  round(sum(r["solar_kwh"]       for r in rows), 2),
            "total_load_kwh":   round(sum(r["load_kwh"]        for r in rows), 2),
            "total_import_kwh": round(sum(r["grid_import_kwh"] for r in rows), 2),
            "total_export_kwh": round(sum(r["grid_export_kwh"] for r in rows), 2),
            "avg_load_kw":      round(sum(r["load_kw"]         for r in rows) / len(rows), 3),
            "self_sufficiency_pct": _self_suf(rows),
        })
    return _write(records, out / "by_wealth.json")


# ── 6. Battery SOC over time ──────────────────────────────────────────────── #
def _battery_soc(household_log: list[dict], out: Path) -> Path:
    records = [
        {
            "hour":           r["hour"],
            "day":            r["day"],
            "hour_of_day":    r["hour_of_day"],
            "household_id":   r["household_id"],
            "household_type": r["household_type"],
            "wealth":         r["wealth"],
            "battery_soc":    r["battery_soc"],
        }
        for r in household_log if r.get("battery_soc") is not None
    ]
    return _write(records, out / "battery_soc.json")


# ── 7. Grid flow over time (neighborhood) ────────────────────────────────── #
def _grid_flow(neighborhood_log: list[dict], out: Path) -> Path:
    records = [
        {
            "hour":          r["hour"],
            "day":           r["day"],
            "hour_of_day":   r["hour_of_day"],
            "import_kwh":    r["total_import_kwh"],
            "export_kwh":    r["total_export_kwh"],
            "net_flow_kwh":  round(r["total_export_kwh"] - r["total_import_kwh"], 3),
            "cloud_coverage": r["cloud_coverage"],
        }
        for r in neighborhood_log
    ]
    return _write(records, out / "grid_flow.json")


# ── 8. Household summaries ────────────────────────────────────────────────── #
def _summaries(summaries: list[dict], out: Path) -> Path:
    flat = []
    for s in summaries:
        row = {
            "household_id":   s["household_id"],
            "household_type": s["household_type"],
            "wealth":         s["wealth"],
            "strategy":       s["strategy"],
        }
        for key in ("solar", "battery", "inverter", "load", "grid"):
            if key in s:
                for k, v in s[key].items():
                    row[f"{key}_{k}"] = v
        flat.append(row)
    return _write(flat, out / "household_summaries.json")


# ── 9. Strategy comparison ────────────────────────────────────────────────── #
def _strategy_comparison(summaries: list[dict], out: Path) -> Path:
    by_strategy = defaultdict(lambda: {"total_cost": 0, "total_revenue": 0,
                                        "total_import": 0, "total_export": 0})
    for s in summaries:
        strat = s["strategy"]
        g     = s.get("grid", {})
        by_strategy[strat]["total_cost"]    += g.get("total_cost",          0)
        by_strategy[strat]["total_revenue"] += g.get("total_revenue",       0)
        by_strategy[strat]["total_import"]  += g.get("total_imported_kwh",  0)
        by_strategy[strat]["total_export"]  += g.get("total_exported_kwh",  0)

    records = []
    for strat, vals in by_strategy.items():
        records.append({
            "strategy":       strat,
            "total_cost":     round(vals["total_cost"],    2),
            "total_revenue":  round(vals["total_revenue"], 2),
            "net_cost":       round(vals["total_cost"] - vals["total_revenue"], 2),
            "total_import":   round(vals["total_import"],  2),
            "total_export":   round(vals["total_export"],  2),
        })
    return _write(records, out / "strategy_comparison.json")


# ── 10. Neighborhood hourly series ───────────────────────────────────────── #
def _neighborhood_series(neighborhood_log: list[dict], out: Path) -> Path:
    return _write(neighborhood_log, out / "neighborhood_series.json")


# ─────────────────────────────────────────────────────────────────────────── #
def _self_suf(rows: list[dict]) -> float:
    """Self-sufficiency = (total_solar - export) / total_load × 100."""
    solar  = sum(r["solar_kwh"]       for r in rows)
    load   = sum(r["load_kwh"]        for r in rows)
    export = sum(r["grid_export_kwh"] for r in rows)
    if load == 0:
        return 0.0
    return round(((solar - export) / load) * 100, 1)