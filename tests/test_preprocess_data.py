
from __future__ import annotations

import pandas as pd
import pytest

from src.preprocess_data import StationRawData, determine_common_period


def _make_station(station_id, gw_start, gw_end):
    index = pd.date_range(gw_start, gw_end, freq="D")
    gw = pd.Series(range(len(index)), index=index, dtype="float64")
    precip = pd.Series(0.0, index=index)
    return StationRawData(
        station_id=station_id, station_name=station_id,
        precip_local=precip, gw=gw, gw_native_resolution="daily total",
    )


def test_determine_common_period_is_the_intersection_of_all_stations():
    a = _make_station("a", "2024-01-01", "2024-12-31")
    b = _make_station("b", "2024-03-01", "2025-06-30")
    c = _make_station("c", "2024-02-01", "2024-11-30")

    start, end = determine_common_period([a, b, c])
    assert start == pd.Timestamp("2024-03-01")  # latest of the three start dates
    assert end == pd.Timestamp("2024-11-30")    # earliest of the three end dates


def test_determine_common_period_raises_when_no_overlap_exists():
    a = _make_station("a", "2024-01-01", "2024-03-01")
    b = _make_station("b", "2024-06-01", "2024-12-31")
    with pytest.raises(ValueError):
        determine_common_period([a, b])
