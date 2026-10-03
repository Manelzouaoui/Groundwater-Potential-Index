from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from .pipeline import CalibrationResult, StationBundle


def plot_correlation_matrix_figure(
    result: CalibrationResult,
    station_name: str,
    save_path: Path | None = None,
) -> plt.Figure:
    """Figure 3: two-dimensional Pearson correlation matrix (N x L)."""
    matrix = result.matrix
    n_star, l_star, r_star = result.n_star, result.l_star, result.r_star

    fig, ax = plt.subplots(figsize=(9, 5.5))
    values = matrix.values
    vmin, vmax = np.nanmin(values), np.nanmax(values)

    im = ax.imshow(values, cmap="RdYlGn", aspect="auto", vmin=vmin, vmax=vmax)

    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(
        [f"L = {int(l)} month" if int(l) == 1 else f"L = {int(l)} months" for l in matrix.columns],
        fontsize=9,
    )
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([f"N = {int(n)} months" for n in matrix.index], fontsize=9)
    ax.set_xlabel("Geological Lag (L)", fontsize=10)
    ax.set_ylabel("Hydrological Memory (N)", fontsize=10)
    ax.set_title(f"2D Pearson Correlation Matrix - {station_name}", fontsize=12, fontweight="bold")

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            value = values[i, j]
            if np.isnan(value):
                continue
            normalized = (value - vmin) / (vmax - vmin) if vmax != vmin else 0.5
            text_color = "white" if normalized < 0.35 else "black"
            is_best = int(matrix.index[i]) == n_star and int(matrix.columns[j]) == l_star
            ax.text(j, i, f"{value:.4f}", ha="center", va="center", fontsize=10,
                    color=text_color, fontweight="bold" if is_best else "normal")

    best_row = list(matrix.index).index(n_star)
    best_col = list(matrix.columns).index(l_star)
    ax.add_patch(patches.Rectangle((best_col - 0.5, best_row - 0.5), 1, 1,
                                    fill=False, edgecolor="blue", linewidth=3))
    ax.annotate(
        f"Optimal calibration\nN = {n_star} months\nL = {l_star} months\nr = {r_star:.4f}",
        xy=(best_col, best_row), xytext=(best_col + 1.2, best_row - 1.0),
        fontsize=9, fontweight="bold", color="blue",
        arrowprops=dict(arrowstyle="->", color="blue", linewidth=1.5),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="blue"),
    )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Pearson Correlation (r)", fontsize=10)

    ax.set_xticks(np.arange(-0.5, len(matrix.columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(matrix.index), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    plt.tight_layout()
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_r_vs_lag_figure(
    result: CalibrationResult,
    station_name: str,
    save_path: Path | None = None,
) -> plt.Figure:
    """Figure 4: Pearson's r as a function of the geological lag L, one curve per N."""
    calibration_long = result.calibration_long
    n_star, l_star, r_star = result.n_star, result.l_star, result.r_star

    fig, ax = plt.subplots(figsize=(8, 5))
    for n in sorted(calibration_long["N"].unique()):
        data_n = calibration_long[calibration_long["N"] == n].sort_values("L")
        ax.plot(data_n["L"], data_n["pearson_r"], marker="o", linewidth=1.8,
                markersize=5, label=f"N = {int(n)} months")

    ax.scatter([l_star], [r_star], marker="*", s=150, zorder=10,
               label=f"Optimum: N*={n_star}, L*={l_star}, r={r_star:.4f}")

    ax.annotate(
        f"Optimal configuration\nN* = {n_star} months\nL* = {l_star} months\nr = {r_star:.4f}",
        xy=(l_star, r_star), xytext=(20, -45), textcoords="offset points",
        fontsize=9, ha="left", va="top", arrowprops=dict(arrowstyle="->", linewidth=1),
    )

    ax.set_xlabel("Geological lag L (months)", fontsize=10)
    ax.set_ylabel("Pearson correlation coefficient r", fontsize=10)
    ax.set_title(f"Pearson correlation coefficient vs geological lag - {station_name}",
                 fontsize=12, pad=12)
    ax.set_xticks(sorted(calibration_long["L"].unique()))
    ax.grid(True, axis="y", linestyle=":", linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8.5, frameon=True)
    fig.tight_layout()

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_station_paper_figure(
    bundle: StationBundle,
    result: CalibrationResult,
    geology_label: str,
    save_path_png: Path | None = None,
    save_path_pdf: Path | None = None,
) -> plt.Figure:
  
    precip, gw = bundle.precip, bundle.gw
    hydro = result.hydro
    comparison = result.comparison
    start, end = bundle.start, bundle.end
    n_star, l_star = result.n_star, result.l_star
    r_display = result.computed_r if not np.isnan(result.computed_r) else result.r_star

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
        "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    })

    fig = plt.figure(figsize=(14, 8.5), facecolor="white")
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1.00, 0.78, 0.78], hspace=0.45, wspace=0.20)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])
    ax_d = fig.add_subplot(gs[2, :])

    ax_a.bar(precip.index, precip.values, width=1.0, color="#B7DDF2", edgecolor="none",
             alpha=0.95, label="Rainfall (P)")
    ax_a.set_title(f"Raw Observations - {bundle.station_name}\n({geology_label})", fontweight="bold")
    ax_a.text(0.01, 0.97, "(a)", transform=ax_a.transAxes, ha="left", va="top",
              fontsize=10, fontweight="bold")
    ax_a.set_ylabel("Rainfall (mm/day)", color="#1F3A93", fontweight="bold")
    ax_a.tick_params(axis="y", labelcolor="#1F3A93")

    ax_a_gw = ax_a.twinx()
    ax_a_gw.plot(gw.index, gw.values, color="#E31A1C", linewidth=1.7, label="GW Level")
    ax_a_gw.set_ylabel("GW Level (mAOD)", color="#E31A1C", fontweight="bold")
    ax_a_gw.tick_params(axis="y", labelcolor="#E31A1C")

    ax_b.plot(hydro.index, hydro["PET"], color="#6A3D9A", linewidth=1.4, label="Potential ET")
    ax_b.plot(hydro.index, hydro["Effective_Recharge"], color="#33A02C", linewidth=1.5,
              label="Effective Recharge (Re)")
    ax_b.plot(hydro.index, hydro["Precipitation"], color="#1F78B4", linewidth=1.1, alpha=0.75,
              label="Gross Rainfall (P)")
    ax_b.set_title(f"Effective Recharge Balance - {bundle.station_name}\n({geology_label})",
                   fontweight="bold")
    ax_b.text(0.01, 0.97, "(b)", transform=ax_b.transAxes, ha="left", va="top",
              fontsize=10, fontweight="bold")
    ax_b.set_ylabel("Water flux (mm/day)", fontweight="bold")
    ax_b.legend(loc="upper right", frameon=True)

    major_ticks = pd.date_range(start=start, end=end, freq="3MS")
    if len(major_ticks) == 0 or major_ticks[0] > start:
        major_ticks = major_ticks.insert(0, start)

    for ax in [ax_a, ax_b, ax_c, ax_d]:
        ax.set_xlim(start, end)
        ax.set_xticks(major_ticks)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

    ax_c.plot(comparison.index, comparison["GPI"], color="#6A3D9A", linewidth=1.8,
              label=f"Model GPI{n_star}(t)")
    ax_c.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    ax_c.set_title(f"Model Validation (N = {n_star} months, L = {l_star} months, r = {r_display:.4f})",
                   fontweight="bold")
    ax_c.text(0.01, 0.95, "(c)", transform=ax_c.transAxes, ha="left", va="top",
              fontsize=10, fontweight="bold")
    ax_c.set_ylabel("Model GPI", fontweight="bold")
    ax_c.set_ylim(-2.2, 2.2)
    ax_c.set_yticks([-2, -1, 0, 1, 2])
    ax_c.legend(loc="upper right")

    ax_d.plot(comparison.index, comparison["GW"], color="#E31A1C", linewidth=1.7,
              label="Observed Groundwater Level")
    ax_d.set_title(f"Optimal GPI vs. Observed Groundwater Level (r = {r_display:.4f})", fontweight="bold")
    ax_d.set_ylabel("Groundwater Level (mAOD)", fontweight="bold")
    ax_d.set_xlabel("Date", fontweight="bold")
    ax_d.legend(loc="upper right")

    for ax in [ax_a, ax_b, ax_c, ax_d]:
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.25)

    fig.suptitle(f"Hydrological Calibration and Piezometric Evaluation - {bundle.station_name}",
                 fontsize=12, fontweight="bold", y=0.995)
    plt.tight_layout()

    if save_path_png is not None:
        save_path_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path_png, dpi=300, bbox_inches="tight")
    if save_path_pdf is not None:
        save_path_pdf.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path_pdf, dpi=300, bbox_inches="tight")
    return fig


def plot_regional_vs_local_bar(
    station_labels: list[str],
    local_results: dict[str, dict],
    regional_results: dict[str, dict],
    station_order: list[str],
    save_path: Path | None = None,
) -> plt.Figure:

    r_regional = [regional_results[sid]["r_star"] for sid in station_order]
    r_local = [local_results[sid]["r_star"] for sid in station_order]

    x = np.arange(len(station_order))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars_regional = ax.bar(x - width / 2, r_regional, width, color="#6A3D9A",
                            label="Regional precipitation (HadEWP)")
    bars_local = ax.bar(x + width / 2, r_local, width, color="#1F78B4",
                         label="Local precipitation")

    for bars, res in [(bars_regional, regional_results), (bars_local, local_results)]:
        for bar, sid in zip(bars, station_order):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015,
                f"r={res[sid]['r_star']:.4f}\n(N*={res[sid]['N_star']}, L*={res[sid]['L_star']})",
                ha="center", va="bottom", fontsize=7.5,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(station_labels, fontsize=9)
    ax.set_ylabel("Pearson correlation coefficient (r*)", fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.set_title(
        "Comparison of optimal calibration results obtained using regional (HadEWP) "
        "and local precipitation data.",
        fontsize=11, fontweight="bold",
    )
    ax.legend(frameon=True)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.7, alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        fig.savefig(save_path.with_suffix(".pdf"), dpi=300, bbox_inches="tight")
    return fig