"""Produce PNG figures from the district-level NTL panel."""
from __future__ import annotations

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import LogNorm
from rasterio.plot import show

from config import DISTRICTS_SHP, FIGURES, NTL_RASTER, PANEL_CSV, YEAR


def _load() -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    gdf = gpd.read_file(DISTRICTS_SHP)
    df = pd.read_csv(PANEL_CSV)
    merged = gdf.merge(df, on=["region", "province", "district", "gid_3"], how="left")
    return merged, df


def _save(fig: plt.Figure, name: str) -> None:
    path = FIGURES / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def map_choropleth(gdf: gpd.GeoDataFrame, column: str, title: str, fname: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 9))
    gdf.plot(
        column=column,
        ax=ax,
        cmap="inferno",
        scheme="quantiles",
        k=6,
        legend=True,
        edgecolor="white",
        linewidth=0.4,
        legend_kwds={"title": column, "loc": "lower left", "fmt": "{:.1f}"},
    )
    ax.set_title(f"{title} · Lima Metropolitana + Callao · {YEAR}", fontsize=13)
    ax.set_axis_off()
    _save(fig, fname)


def map_raster_with_districts(gdf: gpd.GeoDataFrame, fname: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 9))
    with rasterio.open(NTL_RASTER) as src:
        arr = src.read(1).astype("float64")
        arr = np.where(arr < 0.01, 0.01, arr)  # clamp for log scale
        show(arr, transform=src.transform, ax=ax, cmap="inferno",
             norm=LogNorm(vmin=0.1, vmax=np.nanpercentile(arr, 99.5)))
    gdf.boundary.plot(ax=ax, color="cyan", linewidth=0.5)
    ax.set_title(f"VIIRS Black Marble VNP46A4 · Lima {YEAR}  (log radiance)", fontsize=13)
    ax.set_axis_off()
    _save(fig, fname)


def bar_top_districts(df: pd.DataFrame, fname: str, n: int = 20) -> None:
    top = df.sort_values("ntl_mean", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.barh(top["district"], top["ntl_mean"], color="#d95f02")
    ax.set_xlabel("NTL mean (nW·cm\u207B\u00B2·sr\u207B\u00B9)")
    ax.set_title(f"Top {n} distritos por luminosidad media · {YEAR}")
    ax.grid(axis="x", alpha=0.3)
    _save(fig, fname)


def scatter_area_vs_ntl(df: pd.DataFrame, fname: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df["area_km2"], df["ntl_mean"], s=30, color="#1b9e77", alpha=0.8)
    for _, r in df.iterrows():
        if r["ntl_mean"] > df["ntl_mean"].quantile(0.9) or r["area_km2"] > df["area_km2"].quantile(0.9):
            ax.annotate(r["district"], (r["area_km2"], r["ntl_mean"]), fontsize=7, alpha=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("Área (km², escala log)")
    ax.set_ylabel("NTL mean")
    ax.set_title(f"Área distrital vs. luminosidad media · Lima {YEAR}")
    ax.grid(alpha=0.3)
    _save(fig, fname)


def main() -> None:
    gdf, df = _load()
    print("Generating figures...")
    map_raster_with_districts(gdf, f"01_raster_overlay_{YEAR}.png")
    map_choropleth(gdf, "ntl_mean", "NTL mean", f"02_choropleth_ntl_mean_{YEAR}.png")
    map_choropleth(gdf, "ntl_per_km2", "NTL per km2", f"03_choropleth_ntl_per_km2_{YEAR}.png")
    bar_top_districts(df, f"04_top20_districts_{YEAR}.png")
    scatter_area_vs_ntl(df, f"05_area_vs_ntl_{YEAR}.png")
    print("Done.")


if __name__ == "__main__":
    main()
