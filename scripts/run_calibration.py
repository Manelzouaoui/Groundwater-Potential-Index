#!/usr/bin/env python3

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.pipeline import GpiPipeline
from src.utils import REPO_ROOT, get_logger

logger = get_logger(__name__)

RESULTS_DIR = REPO_ROOT / "results"

# Study period shared by the three main calibration stations. Kept
# identical to the notebook's STUDY_PERIODS to avoid introducing a second,
# silently divergent definition of the same period.
STATION_IDS = ["chilgrove_house", "roman_road", "hyde_cottages_risby"]
STUDY_PERIODS = {
    "chilgrove_house": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
    "roman_road": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
    "hyde_cottages_risby": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
}
KEMPS_DRIFT_ID = "kemps_drift"
KEMPS_START = pd.Timestamp("2024-01-01")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = GpiPipeline()

    table4_rows = []

    for station_id in STATION_IDS:
        start, end = STUDY_PERIODS[station_id]
        bundle, result = pipeline.run_station(station_id, start, end)
        result.calibration_long.to_csv(RESULTS_DIR / f"calibration_long_{station_id}.csv", index=False)
        table4_rows.append({
            "station_id": station_id,
            "N_star_months": result.n_star,
            "L_star_months": result.l_star,
            "pearson_r_star": round(result.r_star, 4),
            "n_obs": result.n_obs,
            "period_start": start.date().isoformat(),
            "period_end": end.date().isoformat(),
        })
        logger.info("[%s] N*=%d L*=%d r*=%.4f n_obs=%d",
                    station_id, result.n_star, result.l_star, result.r_star, result.n_obs)

    # Kemps Drift: own observation period, determined from its own data
    # (see src.preprocess_data.determine_common_period), not the shared
    # STUDY_PERIODS above -- Kemps Drift is not part of the common-period
    # set of the other three stations.
    from src.preprocess_data import determine_common_period, load_station_raw_data

    kemps_cfg = pipeline.station_config(KEMPS_DRIFT_ID)
    kemps_raw = load_station_raw_data(kemps_cfg)
    _, kemps_end = determine_common_period([kemps_raw])

    bundle, result = pipeline.run_station(KEMPS_DRIFT_ID, KEMPS_START, kemps_end)
    result.calibration_long.to_csv(RESULTS_DIR / f"calibration_long_{KEMPS_DRIFT_ID}.csv", index=False)
    table4_rows.append({
        "station_id": KEMPS_DRIFT_ID,
        "N_star_months": result.n_star,
        "L_star_months": result.l_star,
        "pearson_r_star": round(result.r_star, 4),
        "n_obs": result.n_obs,
        "period_start": KEMPS_START.date().isoformat(),
        "period_end": kemps_end.date().isoformat(),
    })
    logger.info("[%s] N*=%d L*=%d r*=%.4f n_obs=%d",
                KEMPS_DRIFT_ID, result.n_star, result.l_star, result.r_star, result.n_obs)

    optimal_df = pd.DataFrame(table4_rows)
    optimal_df.to_csv(RESULTS_DIR / "calibration_optimal.csv", index=False)

    # Package every CSV written above into a single archive so the results
    # directory can be handed off or attached as one file.
    zip_path = REPO_ROOT / "results.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for csv_file in sorted(RESULTS_DIR.glob("*.csv")):
            zf.write(csv_file, arcname=csv_file.name)

    print()
    print("Calibration summary:")
    print(optimal_df.to_string(index=False))
    print()
    print(f"CSV files written to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()