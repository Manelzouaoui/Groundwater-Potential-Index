
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calibration import find_optimal_configuration, pivot_correlation_matrix, run_calibration_for_station
from .gpi import align_gpi_and_groundwater, compute_hydrological_memory, standardize_gpi
from .pet import build_daily_pet_series, load_pet_climatology_table
from .preprocess_data import load_station_raw_data
from .utils import get_logger, load_parameters_config, load_stations_config, resolve_path

logger = get_logger(__name__)


MIN_RELIABLE_N_OBS = 30


@dataclass
class StationBundle:
    """Cleaned, period-restricted precipitation / PET / groundwater series for one station."""

    station_id: str
    station_name: str
    start: pd.Timestamp
    end: pd.Timestamp
    precip: pd.Series
    gw: pd.Series
    pet: pd.Series


@dataclass
class CalibrationResult:
    """Calibration outputs for one station, including the reconstructed optimal GPI."""

    station_id: str
    calibration_long: pd.DataFrame
    matrix: pd.DataFrame
    n_star: int
    l_star: int
    r_star: float
    n_obs: int
    hydro: pd.DataFrame
    gpi: pd.Series
    comparison: pd.DataFrame
    computed_r: float


def clean_series(raw_series: pd.Series, clip_lower_zero: bool) -> pd.Series:

    s = pd.Series(raw_series, dtype="float64").copy()
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    s = s[~s.index.duplicated(keep="first")]
    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    if clip_lower_zero:
        s = s.clip(lower=0)
    return s


class GpiPipeline:


    def __init__(self, stations_cfg: dict | None = None, params_cfg: dict | None = None) -> None:
        self.stations_cfg = stations_cfg or load_stations_config()
        self.params_cfg = params_cfg or load_parameters_config()

        self.n_candidates: list[int] = self.params_cfg["hydrological_memory"]["windows_months"]
        self.l_candidates: list[int] = self.params_cfg["geological_lag"]["months"]
        self.days_per_month: int = self.params_cfg["hydrological_memory"]["days_per_month"]
        self.min_valid_fraction: float = self.params_cfg["effective_recharge"]["min_valid_fraction"]
        self.kc: float = self.params_cfg["effective_recharge"]["kc"]

        self._pet_table = load_pet_climatology_table(
            resolve_path(self.stations_cfg["pet_climatology"]["data_file"])
        )
        self._pet_overrides = self.stations_cfg["pet_climatology"].get("station_overrides", {})

    def station_config(self, station_id: str) -> dict:
        return next(s for s in self.stations_cfg["stations"] if s["id"] == station_id)

    def load_bundle(self, station_id: str, start: pd.Timestamp, end: pd.Timestamp) -> StationBundle:
    
        station_cfg = self.station_config(station_id)
        raw = load_station_raw_data(station_cfg)

        pet_raw = build_daily_pet_series(
            raw.precip_local.index, self._pet_table, station_id, self._pet_overrides.get(station_id)
        )

        precip = clean_series(raw.precip_local, clip_lower_zero=True)
        gw = clean_series(raw.gw, clip_lower_zero=False)
        pet = clean_series(pet_raw, clip_lower_zero=True)

        precip = precip.loc[start:end]
        gw = gw.loc[start:end]
        pet = pet.loc[start:end]

        if len(gw) < MIN_RELIABLE_N_OBS:
            logger.warning(
                "[%s] only %d groundwater observations in %s -> %s "
                "(< %d); a correlation computed on such a small sample can "
                "vary substantially between runs and should not be "
                "interpreted as robust.",
                station_id, len(gw), start.date(), end.date(), MIN_RELIABLE_N_OBS,
            )

        return StationBundle(
            station_id=station_id,
            station_name=station_cfg["name"],
            start=start,
            end=end,
            precip=precip,
            gw=gw,
            pet=pet,
        )

    def calibrate(self, bundle: StationBundle) -> CalibrationResult:
        """Run the full (N, L) calibration sweep for one station and
        reconstruct the optimal GPI series (Eq. 1-6).
        """
        precip, gw, pet = bundle.precip, bundle.gw, bundle.pet
        start, end = bundle.start, bundle.end

        calibration_long = run_calibration_for_station(
            station_id=bundle.station_id,
            precip=precip,
            pet=pet,
            gw=gw,
            common_period=(start, end),
            n_candidates=self.n_candidates,
            l_candidates=self.l_candidates,
            kc=self.kc,
            days_per_month_memory=self.days_per_month,
            days_per_month_lag=self.days_per_month,
            min_valid_fraction=self.min_valid_fraction,
        )

        best = find_optimal_configuration(calibration_long)
        matrix = pivot_correlation_matrix(calibration_long).sort_index().sort_index(axis=1)

        n_star = int(best["N"])
        l_star = int(best["L"])
        r_star = float(best["pearson_r"])
        n_obs = int(best["n_obs"])

        # --- reconstruct the optimal GPI, for the four-panel figures ---
        hydro = pd.concat(
            [precip.rename("Precipitation"), pet.rename("PET")], axis=1, join="inner"
        ).dropna()
        hydro["AET"] = self.kc * hydro["PET"]
        hydro["Effective_Recharge"] = (hydro["Precipitation"] - hydro["AET"]).clip(lower=0)

        rmem = compute_hydrological_memory(
            hydro["Effective_Recharge"],
            n_months=n_star,
            days_per_month=self.days_per_month,
            min_valid_fraction=self.min_valid_fraction,
        )

        gpi, mu, sigma = standardize_gpi(rmem, reference_period=None)
        gpi = pd.Series(gpi, dtype="float64")
        gpi.index = pd.to_datetime(gpi.index)
        gpi = gpi.replace([np.inf, -np.inf], np.nan).sort_index()

        comparison = align_gpi_and_groundwater(gpi, gw, l_months=l_star, days_per_month=self.days_per_month)
        comparison = comparison.rename(columns={"gpi": "GPI", "gw": "GW"})
        comparison = comparison[["GPI", "GW"]].dropna().sort_index()

        if len(comparison) > 1 and comparison["GW"].std() > 0:
            comparison["GW_std"] = (comparison["GW"] - comparison["GW"].mean()) / comparison["GW"].std()
            computed_r = comparison["GPI"].corr(comparison["GW_std"])
        else:
            comparison["GW_std"] = np.nan
            computed_r = float("nan")

        return CalibrationResult(
            station_id=bundle.station_id,
            calibration_long=calibration_long,
            matrix=matrix,
            n_star=n_star,
            l_star=l_star,
            r_star=r_star,
            n_obs=n_obs,
            hydro=hydro,
            gpi=gpi,
            comparison=comparison,
            computed_r=computed_r,
        )

    def run_station(self, station_id: str, start: pd.Timestamp, end: pd.Timestamp) -> tuple[StationBundle, CalibrationResult]:
        """Convenience wrapper: load a station's bundle and calibrate it in one call."""
        bundle = self.load_bundle(station_id, start, end)
        result = self.calibrate(bundle)
        return bundle, result

    def calibrate_with_alternate_precipitation(
        self, bundle: StationBundle, precip: pd.Series,
    ) -> pd.Series:
  
        calibration_long = run_calibration_for_station(
            station_id=bundle.station_id,
            precip=precip,
            pet=bundle.pet,
            gw=bundle.gw,
            common_period=(bundle.start, bundle.end),
            n_candidates=self.n_candidates,
            l_candidates=self.l_candidates,
            kc=self.kc,
            days_per_month_memory=self.days_per_month,
            days_per_month_lag=self.days_per_month,
            min_valid_fraction=self.min_valid_fraction,
        )
        return find_optimal_configuration(calibration_long)
