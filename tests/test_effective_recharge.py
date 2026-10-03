
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.effective_recharge import compute_actual_evapotranspiration, compute_effective_recharge


def _daily_series(values, start="2024-01-01"):
    index = pd.date_range(start, periods=len(values), freq="D")
    return pd.Series(values, index=index, dtype="float64")


def test_actual_evapotranspiration_is_kc_times_pet():
    pet = _daily_series([2.0, 4.0, 0.0, 10.0])
    aet = compute_actual_evapotranspiration(pet, kc=0.5)
    expected = pd.Series([1.0, 2.0, 0.0, 5.0], index=pet.index, name="aet_mm_day")
    pd.testing.assert_series_equal(aet, expected)


def test_actual_evapotranspiration_warns_outside_typical_range(caplog):
    pet = _daily_series([1.0, 2.0])
    with caplog.at_level("WARNING"):
        compute_actual_evapotranspiration(pet, kc=3.0)
    assert any("outside the typical" in record.message for record in caplog.records)


def test_effective_recharge_clips_negative_balance_to_zero():
    precip = _daily_series([0.0, 5.0, 10.0])
    aet = _daily_series([2.0, 5.0, 3.0])
    reff = compute_effective_recharge(precip, aet)
    # day 1: 0 - 2 = -2 -> clipped to 0
    # day 2: 5 - 5 = 0
    # day 3: 10 - 3 = 7
    expected = pd.Series([0.0, 0.0, 7.0], index=precip.index, name="reff_mm_day")
    pd.testing.assert_series_equal(reff, expected)


def test_effective_recharge_never_negative_on_random_data():
    rng = np.random.default_rng(0)
    precip = _daily_series(rng.uniform(0, 20, size=200))
    aet = _daily_series(rng.uniform(0, 10, size=200))
    reff = compute_effective_recharge(precip, aet)
    assert (reff >= 0).all()


def test_effective_recharge_missing_input_propagates_as_nan():
    precip = _daily_series([1.0, 2.0, 3.0])
    aet = _daily_series([1.0, np.nan, 1.0])
    reff = compute_effective_recharge(precip, aet)
    assert pd.isna(reff.iloc[1])
    assert reff.iloc[0] == 0.0
    assert reff.iloc[2] == 2.0
