#!/usr/bin/env python3


from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.pipeline import GpiPipeline
from src.preprocess_data import determine_common_period, load_regional_precipitation, load_station_raw_data
from src.pipeline import clean_series
from src.utils import REPO_ROOT, get_logger, resolve_path
from src.visualization import plot_regional_vs_local_bar

logger = get_logger(__name__)

RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = REPO_ROOT / "figures"

STATION_IDS = ["chilgrove_house", "roman_road", "hyde_cottages_risby"]
STUDY_PERIODS = {
    "chilgrove_house": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
    "roman_road": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
    "hyde_cottages_risby": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
}
KEMPS_DRIFT_ID = "kemps_drift"
KEMPS_START = pd.Timestamp("2023-01-01")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = GpiPipeline()

    bundles = {}
    local_results = {}

    for station_id in STATION_IDS:
        start, end = STUDY_PERIODS[station_id]
        bundle, result = pipeline.run_station(station_id, start, end)
        bundles[station_id] = bundle
        local_results[station_id] = {"r_star": result.r_star, "N_star": result.n_star, "L_star": result.l_star}

    kemps_cfg = pipeline.station_config(KEMPS_DRIFT_ID)
    kemps_raw = load_station_raw_data(kemps_cfg)
    _, kemps_end = determine_common_period([kemps_raw])
    kemps_bundle, kemps_result = pipeline.run_station(KEMPS_DRIFT_ID, KEMPS_START, kemps_end)
    bundles[KEMPS_DRIFT_ID] = kemps_bundle
    local_results[KEMPS_DRIFT_ID] = {
        "r_star": kemps_result.r_star, "N_star": kemps_result.n_star, "L_star": kemps_result.l_star,
    }

    # Regional precipitation series (HadEWP), shared across all stations.
    hadewp_path = resolve_path(pipeline.stations_cfg["regional_precipitation"]["data_file"])
    regional_series = load_regional_precipitation(hadewp_path)

    station_order = STATION_IDS + [KEMPS_DRIFT_ID]
    regional_results = {}
    rows = []
    for station_id in station_order:
        bundle = bundles[station_id]
        regional_precip_raw = regional_series.reindex(bundle.precip.index)
        regional_precip = clean_series(regional_precip_raw, clip_lower_zero=True).loc[bundle.start:bundle.end]

        best = pipeline.calibrate_with_alternate_precipitation(bundle, regional_precip)
        regional_results[station_id] = {
            "r_star": float(best["pearson_r"]), "N_star": int(best["N"]), "L_star": int(best["L"]),
        }

        rows.append({
            "station_id": station_id,
            "N_star_local": local_results[station_id]["N_star"],
            "L_star_local": local_results[station_id]["L_star"],
            "r_star_local": round(local_results[station_id]["r_star"], 4),
            "N_star_regional": regional_results[station_id]["N_star"],
            "L_star_regional": regional_results[station_id]["L_star"],
            "r_star_regional": round(regional_results[station_id]["r_star"], 4),
        })
        logger.info(
            "[%s] local: N*=%d L*=%d r*=%.4f | regional: N*=%d L*=%d r*=%.4f",
            station_id,
            local_results[station_id]["N_star"], local_results[station_id]["L_star"], local_results[station_id]["r_star"],
            regional_results[station_id]["N_star"], regional_results[station_id]["L_star"], regional_results[station_id]["r_star"],
        )

    sensitivity_df = pd.DataFrame(rows)
    sensitivity_df.to_csv(RESULTS_DIR / "sensitivity_regional_vs_local.csv", index=False)

    labels = [bundles[sid].station_name for sid in station_order]
    plot_regional_vs_local_bar(
        labels, local_results, regional_results, station_order,
        save_path=FIGURES_DIR / "figure_8_regional_vs_local.png",
    )

    print(sensitivity_df.to_string(index=False))
    print(f"\nWritten to: {RESULTS_DIR / 'sensitivity_regional_vs_local.csv'}")
    print(f"Figure 8 written to: {FIGURES_DIR / 'figure_8_regional_vs_local.png'}")


if __name__ == "__main__":
    main()
