# CERRA vs ERA5 — 2021-01, dominio iberia

Generado por `scripts/cerra.py compare`. CERRA regrideado con `cdo remapcon` a la rejilla ERA5 0,25° del proyecto; 124 instantes (00/06/12/18 UTC).

## Rejilla CERRA original (`cdo griddes`)

```
gridtype  = projection
gridsize  = 1142761
xsize     = 1069
ysize     = 1069
xinc      = 5500
yinc      = 5500
grid_mapping_name = lambert_conformal_conic
standard_parallel = 50.
longitude_of_central_meridian = 8.
latitude_of_projection_origin = 50.
earth_radius = 6371229.
```

## CERRA − ERA5

| variable | unidades | bias medio | RMSE | máx. abs | corr. espacial (media temporal) |
|---|---|---|---|---|---|
| t2m | K | -0.39 | 1.38 | 11.80 | 0.991 |
| msl | Pa | -14.46 | 58.43 | 493.41 | 0.993 |

Bias de 2t por hora: 00 UTC -0.39 K · 06 UTC -0.19 K · 12 UTC -0.36 K · 18 UTC -0.59 K

![2t](cerra_vs_era5_2t.png)
