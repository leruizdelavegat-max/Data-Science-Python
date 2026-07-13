"""Download GADM 4.1 Peru ADM3 and keep Lima Metropolitana + Callao districts.

Notes
-----
GADM 4.1 splits Lima in two parents at NAME_1 level:
  - "Lima Province"  -> Lima Metropolitana (43 districts) *
  - "Lima"           -> rest of Lima department (NOT used here)
  - "Callao"         -> Callao constitutional province (2 polygons in GADM:
                         "Callao" and "Ventanilla"; the other 5 small districts
                         are merged into Callao proper)

* 43 districts is the standard Lima Metropolitana count.
"""
from __future__ import annotations

import io
import zipfile
from urllib.request import urlopen

import geopandas as gpd

from config import CRS_GEO, DATA_SHP, DISTRICTS_SHP, GADM_REGIONS

GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_PER_shp.zip"


def download_gadm(dst: str) -> None:
    print(f"Downloading {GADM_URL} ...")
    with urlopen(GADM_URL) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(dst)
    print(f"Extracted GADM archive to {dst}")


def main() -> None:
    gadm_dir = DATA_SHP / "gadm41_PER"
    if not (gadm_dir / "gadm41_PER_3.shp").exists():
        gadm_dir.mkdir(parents=True, exist_ok=True)
        download_gadm(str(gadm_dir))

    adm3 = gpd.read_file(gadm_dir / "gadm41_PER_3.shp")
    print(f"Peru ADM3 rows: {len(adm3)} | CRS: {adm3.crs}")

    mask = adm3["NAME_1"].isin(GADM_REGIONS)
    lima = adm3.loc[mask, ["NAME_1", "NAME_2", "NAME_3", "GID_3", "geometry"]].copy()
    lima = lima.rename(
        columns={
            "NAME_1": "region",
            "NAME_2": "province",
            "NAME_3": "district",
            "GID_3": "gid_3",
        }
    )
    lima = lima.to_crs(CRS_GEO).reset_index(drop=True)

    print(f"\nKept {len(lima)} districts:")
    print(lima.groupby("region")["district"].count())

    if DISTRICTS_SHP.exists():
        DISTRICTS_SHP.unlink()
    lima.to_file(DISTRICTS_SHP, layer="districts", driver="GPKG")
    print(f"\nSaved -> {DISTRICTS_SHP}")


if __name__ == "__main__":
    main()
