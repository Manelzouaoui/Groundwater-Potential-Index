

from __future__ import annotations

import pandas as pd

from .utils import get_logger

logger = get_logger(__name__)


def compute_actual_evapotranspiration(pet: pd.Series, kc: float) -> pd.Series:
    """Actual evapotranspiration, AET(t) = Kc * PET(t) (Eq. 1).

    Parameters
    ----------
    pet : daily potential-evapotranspiration series, PET(t), in mm/day.
    kc  : dimensionless land-cover coefficient (config: effective_recharge.kc).

    Returns
    -------
    AET(t) series in mm/day, same index as `pet`.
    """
    if not (0.0 < kc <= 2.0):
        logger.warning("Kc=%.3f is outside the typical [0, 2] range for a crop coefficient.", kc)
    aet = kc * pet
    aet.name = "aet_mm_day"
    return aet


def compute_effective_recharge(precip: pd.Series, aet: pd.Series) -> pd.Series:
    """Effective recharge balance, Reff(t) = max(0, P(t) - AET(t)) (Eq. 2).

    Parameters
    ----------
    precip : daily precipitation series, P(t), in mm/day.
    aet    : daily actual-evapotranspiration series, AET(t), in mm/day
             (output of compute_actual_evapotranspiration).

    Returns
    -------
    Reff(t) series in mm/day, aligned on the union of both input indices.
    Days where P(t) or AET(t) is missing produce Reff(t) = NaN (no value is
    invented for a missing input).
    """
    precip_aligned, aet_aligned = precip.align(aet, join="outer")
    balance = precip_aligned - aet_aligned
    reff = balance.clip(lower=0.0)
    reff.name = "reff_mm_day"
    return reff
