
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.gpi import align_gpi_and_groundwater, compute_hydrological_memory, standardize_gpi


def _daily_series(values, start="2024-01-01"):
    index = pd.date_range(start, periods=len(values), freq="D")
    return pd.Series(values, index=index, dtype="float64")


def test_hydrological_memory_is_trailing_mean_over_window():
    # Constant Reff of 2.0 mm/day: any window mean should equal 2.0 once
    # min_periods is satisfied.
    reff = _daily_series([2.0] * 100)
    rmem = compute_hydrological_memory(reff, n_months=3, days_per_month=30, min_valid_fraction=0.7)
    window_days = 3 * 30
    valid = rmem.dropna()
    assert len(valid) == 100 - (int(np.ceil(0.7 * window_days)) - 1)
    assert np.allclose(valid.to_numpy(), 2.0)


def test_hydrological_memory_respects_min_valid_fraction():
    n_days = 60
    reff = _daily_series([1.0] * n_days)
    # Poke a large gap of NaNs near the start of the series.
    reff.iloc[5:50] = np.nan
    rmem = compute_hydrological_memory(reff, n_months=1, days_per_month=30, min_valid_fraction=0.7)
    # A 30-day window with more than 30% NaNs must remain NaN.
    assert pd.isna(rmem.iloc[35])


def test_standardize_gpi_reference_period_matches_full_series_by_default():
    values = np.linspace(0, 10, 50)
    rmem = _daily_series(values)
    gpi, mu, sigma = standardize_gpi(rmem, reference_period=None)
    assert mu == pytest.approx(rmem.mean())
    assert sigma == pytest.approx(rmem.std())
    assert gpi.mean() == pytest.approx(0.0, abs=1e-8)


def test_standardize_gpi_uses_only_reference_period_for_mu_sigma():
    values = list(range(1, 11))  # 1..10
    rmem = _daily_series(values)
    ref_start, ref_end = rmem.index[0], rmem.index[4]  # first 5 values: 1..5
    gpi, mu, sigma = standardize_gpi(rmem, reference_period=(ref_start, ref_end))
    expected_mu = np.mean([1, 2, 3, 4, 5])
    expected_sigma = np.std([1, 2, 3, 4, 5], ddof=1)
    assert mu == pytest.approx(expected_mu)
    assert sigma == pytest.approx(expected_sigma)
    # gpi is still computed over the FULL series using this fixed mu/sigma.
    assert len(gpi) == len(rmem)


def test_standardize_gpi_raises_on_zero_variance():
    rmem = _daily_series([5.0] * 10)
    with pytest.raises(ValueError):
        standardize_gpi(rmem, reference_period=None)


def test_align_gpi_and_groundwater_shifts_gw_forward_by_l_months():
    gpi = _daily_series(np.arange(100, dtype="float64"))
    gw = _daily_series(np.arange(100, dtype="float64") * 10)

    aligned_l0 = align_gpi_and_groundwater(gpi, gw, l_months=0, days_per_month=30)
    assert (aligned_l0["gpi"] * 10 == aligned_l0["gw"]).all()

    # With L=1 month (30 days), gpi(t) should be paired with gw(t + 30).
    aligned_l1 = align_gpi_and_groundwater(gpi, gw, l_months=1, days_per_month=30)
    t0 = aligned_l1.index[0]
    expected_gw = gw.loc[t0 + pd.Timedelta(days=30)]
    assert aligned_l1.loc[t0, "gw"] == expected_gw


def test_align_gpi_and_groundwater_drops_rows_without_real_observations():
    gpi = _daily_series(np.arange(30, dtype="float64"))
    gw = _daily_series([1.0, np.nan, 3.0])  # sparse groundwater series
    aligned = align_gpi_and_groundwater(gpi, gw, l_months=0, days_per_month=30)
    assert len(aligned) == 2  # only the two real (non-NaN) GW observations
    assert not aligned["gw"].isna().any()


def test_align_gpi_and_groundwater_handles_irregular_sparse_index():
    # Simulate manually-dipped groundwater readings at irregular dates.
    gpi = pd.Series(
        np.arange(200, dtype="float64"),
        index=pd.date_range("2024-01-01", periods=200, freq="D"),
    )
    sparse_dates = pd.to_datetime(["2024-02-01", "2024-04-15", "2024-06-20"])
    gw = pd.Series([100.0, 200.0, 300.0], index=sparse_dates)

    aligned = align_gpi_and_groundwater(gpi, gw, l_months=1, days_per_month=30)
    assert len(aligned) == 3
    for date, value in zip(sparse_dates, [100.0, 200.0, 300.0]):
        shifted_date = date - pd.Timedelta(days=30)
        assert aligned.loc[shifted_date, "gw"] == value
