"""Shared configuration for the Lima nighttime-lights pipeline."""
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

BLACKMARBLE_TOKEN = os.getenv("BLACKMARBLE_TOKEN")
if not BLACKMARBLE_TOKEN:
    raise RuntimeError("BLACKMARBLE_TOKEN is missing. Put it in ntl_lima/.env")

DATA_RAW = ROOT / "data" / "raw"
DATA_SHP = ROOT / "data" / "shp"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"

for d in (DATA_RAW, DATA_SHP, OUTPUTS, FIGURES):
    d.mkdir(parents=True, exist_ok=True)

YEAR = 2024
PRODUCT_ID = "VNP46A4"

DISTRICTS_SHP = DATA_SHP / "lima_callao_districts.gpkg"
NTL_RASTER = DATA_RAW / f"ntl_{PRODUCT_ID}_{YEAR}.tif"
PANEL_CSV = OUTPUTS / f"panel_ntl_lima_{YEAR}.csv"

CRS_GEO = "EPSG:4326"
CRS_METRIC = "EPSG:32718"

GADM_REGIONS = ["Lima Province", "Callao"]
