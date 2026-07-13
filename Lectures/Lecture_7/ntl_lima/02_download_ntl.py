"""Download annual VIIRS Black Marble (VNP46A4) h5 tiles for Lima + Callao
and build a clipped, scaled GeoTIFF.

Why direct download instead of blackmarblepy?
  NASA deprecated the `/api/v1/files` search endpoint that `blackmarblepy`
  depends on (returns 404 as of 2026). The HDF5 tiles themselves are still
  served from `/archive/allData/5200/VNP46A4/<year>/001/` with bearer-token
  auth, so we fetch the two tiles covering Lima (h10v07, h10v08), read the
  `NearNadir_Composite_Snow_Free` radiance band, apply the scale factor,
  mosaic the tiles, and clip to the ROI.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

import geopandas as gpd
import h5py
import numpy as np
import rasterio
from rasterio.merge import merge as rio_merge
from rasterio.transform import from_bounds

from config import (
    BLACKMARBLE_TOKEN,
    DATA_RAW,
    DISTRICTS_SHP,
    NTL_RASTER,
    YEAR,
)

BASE = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5200/VNP46A4"
TILES = ["h10v10"]  # single 10°x10° tile covering Lima (-80..-70 lon, -20..-10 lat)
VAR = "NearNadir_Composite_Snow_Free"
GRID_GROUP = "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d"


def _http_get(url: str, dst: Path | None = None) -> bytes | None:
    req = Request(url, headers={"Authorization": f"Bearer {BLACKMARBLE_TOKEN}"})
    with urlopen(req, timeout=120) as resp:
        if dst is None:
            return resp.read()
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        return None


def _list_tile_files(year: int) -> list[str]:
    import json
    url = f"{BASE}/{year}/001.json"
    data = json.loads(_http_get(url))
    return [e["name"] for e in data.get("content", [])]


def _download_tile(filename: str, year: int, dst_dir: Path) -> Path:
    dst = dst_dir / filename
    if dst.exists() and dst.stat().st_size > 0:
        print(f"  cached: {filename}")
        return dst
    url = f"{BASE}/{year}/001/{filename}"
    print(f"  downloading {filename} ...")
    t0 = time.time()
    _http_get(url, dst=dst)
    print(f"    {dst.stat().st_size/1e6:.1f} MB in {time.time()-t0:.1f}s")
    return dst


def _h5_to_geotiff(h5_path: Path, tif_path: Path) -> Path:
    with h5py.File(h5_path, "r") as f:
        ds = f[f"{GRID_GROUP}/Data Fields/{VAR}"]
        arr = ds[:]
        scale = float(np.ravel(ds.attrs.get("scale_factor", [1.0]))[0])
        offset = float(np.ravel(ds.attrs.get("offset", [0.0]))[0])
        fill = float(np.ravel(ds.attrs.get("_FillValue", [-999.9]))[0])
        west = float(f.attrs["WestBoundingCoord"])
        east = float(f.attrs["EastBoundingCoord"])
        north = float(f.attrs["NorthBoundingCoord"])
        south = float(f.attrs["SouthBoundingCoord"])

    arr = arr.astype("float32")
    arr[arr == fill] = np.nan
    arr = arr * scale + offset

    height, width = arr.shape
    transform = from_bounds(west, south, east, north, width, height)
    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=np.nan,
        compress="DEFLATE",
    ) as dst:
        dst.write(arr, 1)
    return tif_path


def main() -> None:
    if not DISTRICTS_SHP.exists():
        raise FileNotFoundError(f"Run 01_download_districts.py first ({DISTRICTS_SHP}).")

    gdf = gpd.read_file(DISTRICTS_SHP)
    minx, miny, maxx, maxy = gdf.total_bounds
    # pad by ~1 pixel (~0.005 deg) so ROI isn't flush with raster edge
    pad = 0.01
    minx, miny, maxx, maxy = minx - pad, miny - pad, maxx + pad, maxy + pad
    print(f"ROI bbox: {minx:.3f},{miny:.3f},{maxx:.3f},{maxy:.3f}")

    print(f"\nListing VNP46A4/{YEAR}/001 file index ...")
    all_files = _list_tile_files(YEAR)

    tile_tifs: list[Path] = []
    for tile in TILES:
        pattern = re.compile(rf"VNP46A4\.A{YEAR}001\.{tile}\.\d+\.\d+\.h5$")
        match = next((n for n in all_files if pattern.match(n)), None)
        if match is None:
            raise RuntimeError(f"No VNP46A4 file found for tile {tile} in {YEAR}.")
        h5_path = _download_tile(match, YEAR, DATA_RAW)
        tif_path = DATA_RAW / (h5_path.stem + ".tif")
        print(f"  -> building GeoTIFF {tif_path.name}")
        _h5_to_geotiff(h5_path, tif_path)
        tile_tifs.append(tif_path)

    print("\nMosaicking tiles and clipping to ROI ...")
    srcs = [rasterio.open(p) for p in tile_tifs]
    mosaic, transform = rio_merge(srcs, bounds=(minx, miny, maxx, maxy))
    meta = srcs[0].meta.copy()
    for s in srcs:
        s.close()
    meta.update(
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=transform,
        compress="DEFLATE",
    )
    with rasterio.open(NTL_RASTER, "w", **meta) as dst:
        dst.write(mosaic)
    print(f"Saved -> {NTL_RASTER}  shape={mosaic.shape}")


if __name__ == "__main__":
    main()
