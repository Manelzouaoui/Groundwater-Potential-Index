

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .effective_recharge import compute_actual_evapotranspiration, compute_effective_recharge
from .gpi import align_gpi_and_groundwater, compute_hydrological_memory, standardize_gpi
from .utils import get_logger

logger = get_logger(__name__)

MIN_OBS_FOR_CORRELATION = 3


def compute_reff_series(precip: pd.Series, pet: pd.Series, kc: float) -> pd.Series:
    """Build Reff(t) (Eq. 1-2) from the precipitation and PET series."""
    precip_aligned, pet_aligned = precip.align(pet, join="outer")
    aet = compute_actual_evapotranspiration(pet_aligned, kc)
    reff = compute_effective_recharge(precip_aligned, aet)
    return reff


def evaluate_configuration(
    reff: pd.Series,
    gw: pd.Series,
    n_months: int,
    l_months: int,
    days_per_month: int,
    min_valid_fraction: float,
    common_period: tuple[pd.Timestamp, pd.Timestamp],
) -> dict:
    """Evaluate a single (N, L) configuration: build GPI_N, align with
    GW(t+L), restrict to the common observation period, and compute
    Pearson's r.
    """
    rmem = compute_hydrological_memory(
        reff, n_months, days_per_month=days_per_month, min_valid_fraction=min_valid_fraction
    )
    gpi, mu, sigma = standardize_gpi(rmem, reference_period=common_period)

    aligned = align_gpi_and_groundwater(gpi, gw, l_months, days_per_month=days_per_month)
    start, end = common_period
    aligned = aligned.loc[(aligned.index >= start) & (aligned.index <= end)]

    n_obs = len(aligned)
    if n_obs >= MIN_OBS_FOR_CORRELATION:
        r, p_value = stats.pearsonr(aligned["gpi"], aligned["gw"])
    else:
        r, p_value = np.nan, np.nan
        logger.warning(
            "N=%d, L=%d: only %d overlapping observation(s) within the "
            "common period; Pearson's r not computed (requires >= %d).",
            n_months, l_months, n_obs, MIN_OBS_FOR_CORRELATION,
        )

    return {
        "N": n_months,
        "L": l_months,
        "pearson_r": r,
        "p_value": p_value,
        "n_obs": n_obs,
        "rmem_mu": mu,
        "rmem_sigma": sigma,
    }


def run_calibration_for_station(
    station_id: str,
    precip: pd.Series,
    pet: pd.Series,
    gw: pd.Series,
    common_period: tuple[pd.Timestamp, pd.Timestamp],
    n_candidates: list[int],
    l_candidates: list[int],
    kc: float,
    days_per_month_memory: int,
    days_per_month_lag: int,
    min_valid_fraction: float,
) -> pd.DataFrame:
 
    reff = compute_reff_series(precip, pet, kc)

    records = []
    for n_months in n_candidates:
        for l_months in l_candidates:
            record = evaluate_configuration(
                reff, gw, n_months, l_months,
                days_per_month=days_per_month_memory,
                min_valid_fraction=min_valid_fraction,
                common_period=common_period,
            )
            record["station_id"] = station_id
            records.append(record)

    df = pd.DataFrame.from_records(records)
    logger.info(
        "[%s] %d (N, L) configurations evaluated (N in %s, L in %s)",
        station_id, len(df), n_candidates, l_candidates,
    )
    return df


def find_optimal_configuration(calibration_long: pd.DataFrame) -> pd.Series:

    valid = calibration_long.dropna(subset=["pearson_r"])
    if valid.empty:
        raise ValueError("No valid (N, L) configuration from which to select an optimum.")
    best_idx = valid["pearson_r"].idxmax()
    return calibration_long.loc[best_idx]


def pivot_correlation_matrix(calibration_long: pd.DataFrame) -> pd.DataFrame:
    """Pivot the long-format calibration table into an N x L correlation matrix."""
    return calibration_long.pivot(index="N", columns="L", values="pearson_r")
