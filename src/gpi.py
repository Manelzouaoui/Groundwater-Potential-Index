from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import get_logger

logger = get_logger(__name__)


def compute_hydrological_memory(
    reff: pd.Series,
    n_months: int,
    days_per_month: int = 30,
    min_valid_fraction: float = 1.0,
) -> pd.Series:

    window_days = n_months * days_per_month
    min_periods = max(1, int(np.ceil(min_valid_fraction * window_days)))

    rmem = reff.rolling(window=window_days, min_periods=min_periods).mean()
    rmem.name = f"rmem_N{n_months}"
    return rmem


def standardize_gpi(
    rmem: pd.Series,
    reference_period: tuple[pd.Timestamp, pd.Timestamp] | None = None,
) -> tuple[pd.Series, float, float]:

    if reference_period is not None:
        start, end = reference_period
        reference_values = rmem.loc[start:end]
    else:
        reference_values = rmem

    mu = float(reference_values.mean())
    sigma = float(reference_values.std())

    if sigma == 0 or np.isnan(sigma):
        raise ValueError(
            "The standard deviation of Rmem over the reference period is "
            "zero or NaN; the GPI cannot be standardized. Check the input "
            "effective-recharge series and the reference period."
        )

    gpi = (rmem - mu) / sigma
    gpi.name = "GPI"
    return gpi, mu, sigma


def align_gpi_and_groundwater(
    gpi: pd.Series,
    gw: pd.Series,
    l_months: int,
    days_per_month: int = 30,
) -> pd.DataFrame:

    lag_days = l_months * days_per_month
    # Reindex the groundwater series so that position t holds GW(t + L):
    # shifting the *index* backward by lag_days maps date (t + L) -> date t.
    gw_shifted = gw.copy()
    gw_shifted.index = gw_shifted.index - pd.Timedelta(days=lag_days)
    gw_shifted.name = "gw"

    merged = pd.concat([gpi.rename("gpi"), gw_shifted], axis=1, join="inner")
    merged = merged.dropna(subset=["gpi", "gw"])
    return merged