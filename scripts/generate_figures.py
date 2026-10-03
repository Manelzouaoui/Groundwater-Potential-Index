#!/usr/bin/env python3


from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.pipeline import GpiPipeline
from src.preprocess_data import determine_common_period, load_station_raw_data
from src.utils import REPO_ROOT, get_logger
from src.visualization import (
    plot_correlation_matrix_figure,
    plot_r_vs_lag_figure,
    plot_station_paper_figure,
)

logger = get_logger(__name__)

FIGURES_DIR = REPO_ROOT / "figures"

STATION_IDS = ["chilgrove_house", "roman_road", "hyde_cottages_risby"]
STUDY_PERIODS = {
    "chilgrove_house": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
    "roman_road": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
    "hyde_cottages_risby": (pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-10")),
}
GEOLOGY_LABELS = {
    "roman_road": "West - Moor Cliffs Formation",
    "hyde_cottages_risby": "East - Unconfined Chalk",
    "kemps_drift": "North Yorkshire - Sherwood Sandstone Group",
}
KEMPS_DRIFT_ID = "kemps_drift"
KEMPS_START = pd.Timestamp("2023-01-01")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = GpiPipeline()

    bundles: dict[str, object] = {}
    results: dict[str, object] = {}

    for station_id in STATION_IDS:
        start, end = STUDY_PERIODS[station_id]
        bundle, result = pipeline.run_station(station_id, start, end)
        bundles[station_id] = bundle
        results[station_id] = result

    chilgrove_result = results["chilgrove_house"]
    plot_correlation_matrix_figure(
        chilgrove_result, bundles["chilgrove_house"].station_name,
        save_path=FIGURES_DIR / "figure_3_chilgrove_house_matrix.png",
    )
    logger.info("Figure 3 saved.")

    plot_r_vs_lag_figure(
        chilgrove_result, bundles["chilgrove_house"].station_name,
        save_path=FIGURES_DIR / "figure_4_chilgrove_house_calibration.png",
    )
    logger.info("Figure 4 saved.")

    for station_id in ["roman_road", "hyde_cottages_risby"]:
        plot_station_paper_figure(
            bundles[station_id], results[station_id], GEOLOGY_LABELS[station_id],
            save_path_png=FIGURES_DIR / f"figure_{station_id}.png",
        )
        logger.info("Figure for %s saved.", station_id)

    kemps_cfg = pipeline.station_config(KEMPS_DRIFT_ID)
    kemps_raw = load_station_raw_data(kemps_cfg)
    _, kemps_end = determine_common_period([kemps_raw])
    kemps_bundle, kemps_result = pipeline.run_station(KEMPS_DRIFT_ID, KEMPS_START, kemps_end)

    plot_station_paper_figure(
        kemps_bundle, kemps_result, GEOLOGY_LABELS[KEMPS_DRIFT_ID],
        save_path_png=FIGURES_DIR / "figure_kemps_drift.png",
    )
    logger.info("Figure 7 (Kemps Drift) saved.")

    print(f"All figures written to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()