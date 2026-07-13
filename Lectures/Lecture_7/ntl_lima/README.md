# NTL Lima — VIIRS Black Marble por distrito (2024)

Pipeline que construye indicadores económicos proxy (luces nocturnas VIIRS
Black Marble, producto anual **VNP46A4**) a nivel distrital para Lima
Metropolitana + Callao.

## Entorno
Conda env: **gis_env** (paquetes clave: geopandas, rasterio, rasterstats,
h5py, rioxarray, matplotlib, mapclassify, python-dotenv).

## Secretos
Tu token NASA Earthdata vive en `ntl_lima/.env`:
```
BLACKMARBLE_TOKEN=...
```
`.env` está ignorado por git.

## Ejecución
```bash
# usar el python de gis_env
PY="C:/Users/Alexander/anaconda3/envs/gis_env/python.exe"
$PY 01_download_districts.py    # distritos GADM -> data/shp/
$PY 02_download_ntl.py          # VNP46A4 2024 -> data/raw/
$PY 03_compute_indicators.py    # zonal stats -> outputs/panel_ntl_lima_2024.csv
$PY 04_plot_maps.py             # figuras -> outputs/figures/*.png
```

## Outputs
- `outputs/panel_ntl_lima_2024.csv` — 45 filas × (region, province, district,
  gid_3, ntl_mean/median/std/sum/min/max, ntl_pixels, area_km2, ntl_per_km2).
- `outputs/figures/01_raster_overlay_2024.png` — raster VIIRS + bordes.
- `outputs/figures/02_choropleth_ntl_mean_2024.png` — luminosidad media.
- `outputs/figures/03_choropleth_ntl_per_km2_2024.png` — densidad lumínica.
- `outputs/figures/04_top20_districts_2024.png` — ranking top 20.
- `outputs/figures/05_area_vs_ntl_2024.png` — área vs. luminosidad.

## Notas técnicas

**Tile VIIRS.** Lima entera cae en un único tile 10°×10° (`h10v10`:
lon −80 a −70, lat −20 a −10).

**API deprecada.** NASA deshabilitó `ladsweb.modaps.eosdis.nasa.gov/api/v1/files`
(el endpoint que usa `blackmarblepy`), por lo que descargamos el `.h5`
directo desde `/archive/allData/5200/VNP46A4/<año>/001/` con el bearer
token, parseamos `HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/NearNadir_Composite_Snow_Free`
y construimos un GeoTIFF en EPSG:4326.

**Limitación GADM 4.1 en Callao.** La capa ADM3 de GADM solo distingue
2 polígonos en la Provincia Constitucional del Callao (`Callao` y
`Ventanilla`), fusionando los 5 restantes (Bellavista, La Perla, La Punta,
Carmen de la Legua, Mi Perú). El polígono `Callao` resultante suele salir
con radiancia media muy baja porque incluye zonas portuarias/marinas mal
delimitadas. Si necesitas los 7 distritos reales del Callao hay que usar
un shapefile INEI oficial (no disponible por URL pública estable al
momento de correr este pipeline).
