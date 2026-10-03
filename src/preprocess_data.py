
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .utils import get_logger, resolve_path

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Raw file loaders
# -----------------------------------------------------------------------------

def _load_ea_measure_csv(path: Path) -> pd.DataFrame:
  
    df = pd.read_csv(path)
    required = {"date", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path}: expected columns missing: {missing}")
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def load_rainfall_series(path: Path) -> pd.Series:

    df = _load_ea_measure_csv(path)
    series = df.groupby(df["date"].dt.normalize())["value"].mean().sort_index()
    series.name = "precip_mm"
    series.index.name = "date"
    return series


def load_groundwater_series(path: Path, native_resolution: str) -> pd.Series:
 
    df = _load_ea_measure_csv(path)
    if "sub-daily" in native_resolution:
        series = df.groupby(df["date"].dt.normalize())["value"].mean().sort_index()
    elif "dip" in native_resolution:
        series = df.groupby(df["date"].dt.normalize())["value"].mean().sort_index()
    else:
        raise ValueError(f"Unrecognized native_resolution: {native_resolution!r}")
    series.name = "gw_mAOD"
    series.index.name = "date"
    return series


def load_regional_precipitation(path: Path) -> pd.Series:

    df = pd.read_csv(
        path,
        skiprows=4,
        sep=r"\s+",
        names=["date", "value"],
        engine="python",
    )
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"])
    series = df.groupby(df["date"].dt.normalize())["value"].mean().sort_index()
    series.name = "precip_regional_mm"
    series.index.name = "date"
    return series


# -----------------------------------------------------------------------------
# Alignment / common period
# -----------------------------------------------------------------------------

@dataclass
class StationRawData:
    station_id: str
    station_name: str
    precip_local: pd.Series
    gw: pd.Series
    gw_native_resolution: str


def load_station_raw_data(station_cfg: dict) -> StationRawData:
    """Load the raw local-rainfall and groundwater-level series for one station."""
    gw_path = resolve_path(station_cfg["groundwater"]["data_file"])
    rain_path = resolve_path(station_cfg["rain_gauge"]["data_file"])

    gw = load_groundwater_series(gw_path, station_cfg["groundwater"]["native_resolution"])
    precip = load_rainfall_series(rain_path)

    logger.info(
        "[%s] GW series loaded: %d obs (%s -> %s); rainfall series: %d obs (%s -> %s)",
        station_cfg["id"], len(gw), gw.index.min().date(), gw.index.max().date(),
        len(precip), precip.index.min().date(), precip.index.max().date(),
    )
    return StationRawData(
        station_id=station_cfg["id"],
        station_name=station_cfg["name"],
        precip_local=precip,
        gw=gw,
        gw_native_resolution=station_cfg["groundwater"]["native_resolution"],
    )


def determine_common_period(all_stations_raw: list[StationRawData]) -> tuple[pd.Timestamp, pd.Timestamp]:

    starts = [s.gw.index.min() for s in all_stations_raw]
    ends = [s.gw.index.max() for s in all_stations_raw]
    common_start, common_end = max(starts), min(ends)
    if common_start > common_end:
        raise ValueError(
            "No common observation period exists across the supplied stations "
            f"(computed start={common_start.date()} > end={common_end.date()})."
        )
    logger.info("Observation period common to all stations: %s -> %s",
                common_start.date(), common_end.date())
    return common_start, common_end
