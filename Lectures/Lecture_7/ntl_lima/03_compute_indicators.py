"""Zonal statistics of VIIRS Black Marble 2024 per district.

Writes a CSV with per-district indicators:
  ntl_mean, ntl_median, ntl_std, ntl_sum, area_km2, ntl_per_km2
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterstats import zonal_stats

from config import CRS_METRIC, DISTRICTS_SHP, NTL_RASTER, PANEL_CSV, YEAR


def main() -> None:
    if not NTL_RASTER.exists():
        raise FileNotFoundError(f"Run 02_download_ntl.py first ({NTL_RASTER}).")
    gdf = gpd.read_file(DISTRICTS_SHP)

    with rasterio.open(NTL_RASTER) as src:
        affine = src.transform
        arr = src.read(1)
        nodata = src.nodata
    # rasterstats needs a masked array or explicit nodata argument
    if nodata is None or not np.isnan(nodata):
        arr = np.where(np.isnan(arr), -9999.0, arr).astype("float32")
        nodata = -9999.0

    stats = zonal_stats(
        gdf,
        arr,
        affine=affine,
        nodata=nodata,
        stats=["mean", "median", "std", "sum", "min", "max", "count"],
        geojson_out=False,
    )
    df = pd.DataFrame(stats)
    df = df.rename(
        columns={
            "mean": "ntl_mean",
            "median": "ntl_median",
            "std": "ntl_std",
            "sum": "ntl_sum",
            "min": "ntl_min",
            "max": "ntl_max",
            "count": "ntl_pixels",
        }
    )

    # District area in km2 using a metric CRS (UTM 18S)
    gdf_m = gdf.to_crs(CRS_METRIC)
    df["area_km2"] = gdf_m.geometry.area.values / 1e6
    df["ntl_per_km2"] = df["ntl_sum"] / df["area_km2"]

    out = pd.concat(
        [gdf[["region", "province", "district", "gid_3"]].reset_index(drop=True), df],
        axis=1,
    )
    out.insert(0, "year", YEAR)
    out = out.sort_values("ntl_mean", ascending=False).reset_index(drop=True)

    out.to_csv(PANEL_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved -> {PANEL_CSV}  rows={len(out)}")
    print("\nTop 10 by ntl_mean:")
    print(out.head(10)[["district", "ntl_mean", "ntl_per_km2", "area_km2"]].to_string(index=False))
    print("\nBottom 5 by ntl_mean:")
    print(out.tail(5)[["district", "ntl_mean", "ntl_per_km2", "area_km2"]].to_string(index=False))


if __name__ == "__main__":
    main()
