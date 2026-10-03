
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.calibration import (
    evaluate_configuration,
    find_optimal_configuration,
    pivot_correlation_matrix,
    run_calibration_for_station,
)


def _daily_series(values, start="2020-01-01"):
    index = pd.date_range(start, periods=len(values), freq="D")
    return pd.Series(values, index=index, dtype="float64")


def test_run_calibration_for_station_evaluates_full_grid():
    n_days = 24 * 30  # long enough for N=12 months windows
    rng = np.random.default_rng(42)
    precip = _daily_series(np.abs(rng.normal(5, 2, n_days)))
    pet = _daily_series(np.abs(rng.normal(2, 1, n_days)))
    gw = _daily_series(rng.normal(50, 1, n_days))

    common_period = (precip.index[0], precip.index[-1])
    n_candidates = [3, 6, 12]
    l_candidates = [0, 1, 2, 3, 4, 5]

    calibration_long = run_calibration_for_station(
        station_id="synthetic",
        precip=precip, pet=pet, gw=gw,
        common_period=common_period,
        n_candidates=n_candidates, l_candidates=l_candidates,
        kc=0.5, days_per_month_memory=30, days_per_month_lag=30,
        min_valid_fraction=0.7,
    )

    assert len(calibration_long) == len(n_candidates) * len(l_candidates)
    assert set(calibration_long["N"].unique()) == set(n_candidates)
    assert set(calibration_long["L"].unique()) == set(l_candidates)
    assert {"pearson_r", "p_value", "n_obs", "rmem_mu", "rmem_sigma"}.issubset(calibration_long.columns)


def test_find_optimal_configuration_selects_the_maximum_r():
    calibration_long = pd.DataFrame({
        "N": [3, 3, 6, 6],
        "L": [0, 1, 0, 1],
        "pearson_r": [0.10, 0.55, 0.40, 0.20],
        "n_obs": [50, 50, 50, 50],
    })
    best = find_optimal_configuration(calibration_long)
    assert best["N"] == 3
    assert best["L"] == 1
    assert best["pearson_r"] == pytest.approx(0.55)


def test_find_optimal_configuration_ignores_nan_rows():
    calibration_long = pd.DataFrame({
        "N": [3, 6],
        "L": [0, 0],
        "pearson_r": [np.nan, 0.30],
        "n_obs": [1, 50],
    })
    best = find_optimal_configuration(calibration_long)
    assert best["N"] == 6


def test_find_optimal_configuration_raises_if_all_nan():
    calibration_long = pd.DataFrame({"N": [3], "L": [0], "pearson_r": [np.nan], "n_obs": [1]})
    with pytest.raises(ValueError):
        find_optimal_configuration(calibration_long)


def test_pivot_correlation_matrix_shape():
    calibration_long = pd.DataFrame({
        "N": [3, 3, 6, 6],
        "L": [0, 1, 0, 1],
        "pearson_r": [0.1, 0.2, 0.3, 0.4],
    })
    matrix = pivot_correlation_matrix(calibration_long)
    assert matrix.shape == (2, 2)
    assert matrix.loc[6, 1] == pytest.approx(0.4)


def test_evaluate_configuration_flags_insufficient_overlap():
    rng = np.random.default_rng(1)
    reff = _daily_series(np.abs(rng.normal(2.0, 0.5, 400)))  # variable, non-degenerate
    gw = _daily_series([50.0, 51.0])  # only 2 observations
    common_period = (reff.index[0], reff.index[-1])
    result = evaluate_configuration(
        reff, gw, n_months=3, l_months=0, days_per_month=30,
        min_valid_fraction=0.7, common_period=common_period,
    )
    assert np.isnan(result["pearson_r"])
    assert result["n_obs"] < 3
