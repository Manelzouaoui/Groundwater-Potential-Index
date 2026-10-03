

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .utils import get_logger

logger = get_logger(__name__)


def load_pet_climatology_table(path: Path) -> pd.DataFrame:

    df = pd.read_csv(path)
    expected_cols = {"stationReference", "month", "avg_daily_pet"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"PET climatology file {path}: missing columns: {missing}")

    # A small number of station codes appear twice per month in the raw
    # file (24 rows instead of 12); these are averaged rather than
    # arbitrarily selecting one.
    df = (
        df.groupby(["stationReference", "month"], as_index=False)["avg_daily_pet"]
        .mean()
    )
    return df


def national_monthly_mean(pet_table: pd.DataFrame) -> pd.Series:

    return pet_table.groupby("month")["avg_daily_pet"].mean()


def station_monthly_climatology(
    pet_table: pd.DataFrame,
    station_override_code: str | None,
) -> pd.Series | None:
 
    if not station_override_code:
        return None
    subset = pet_table[pet_table["stationReference"] == station_override_code]
    if subset.empty:
        logger.warning(
            "PET override code %s not found in the climatology table; "
            "falling back to the national average.",
            station_override_code,
        )
        return None
    return subset.set_index("month")["avg_daily_pet"]


def build_daily_pet_series(
    dates: pd.DatetimeIndex,
    pet_table: pd.DataFrame,
    station_id: str,
    station_override_code: str | None,
) -> pd.Series:

    monthly = station_monthly_climatology(pet_table, station_override_code)
    if monthly is not None:
        logger.info(
            "[%s] Using the station-specific PET climatology (EA code %s).",
            station_id, station_override_code,
        )
    else:
        monthly = national_monthly_mean(pet_table)
        logger.warning(
            "[%s] No geographically matched PET station is available in "
            "the supplied data (no coordinates for the PET station codes); "
            "using the national mean PET climatology as a documented "
            "fallback.",
            station_id,
        )

    months = dates.month
    values = monthly.reindex(months).to_numpy()
    return pd.Series(values, index=dates, name="pet_mm_day")
