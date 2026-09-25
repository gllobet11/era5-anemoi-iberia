# GRIB vs NetCDF — pressure 2020-01

- Ficheros: `pressure_2020-01.grib` (2.5 MB) vs `pressure_2020-01.nc` (1.9 MB, 1 fichero(s) .nc)
- Dims crudas GRIB: `{'time': 124, 'isobaricInhPa': 2, 'latitude': 41, 'longitude': 61}` · NetCDF: `{'valid_time': 124, 'pressure_level': 2, 'latitude': 41, 'longitude': 61}`
- Solo GRIB: [] · solo NetCDF: []
- Pasos de tiempo: GRIB 124 · NetCDF 124 · comunes 124

| Var | dtype GRIB/NC | Máx abs | units GRIB | units NC | Atributos solo en NC |
|---|---|---|---|---|---|
| t | float32/float32 | 0 | K | K | — |
| z | float32/float32 | 0 | m**2 s**-2 | m**2 s**-2 | — |

## Cabecera NetCDF (`ncdump -h`)

```
netcdf pressure_2020-01 {
dimensions:
	valid_time = 124 ;
	pressure_level = 2 ;
	latitude = 41 ;
	longitude = 61 ;
variables:
	int64 number ;
		number:long_name = "ensemble member numerical id" ;
		number:units = "1" ;
		number:standard_name = "realization" ;
	int64 valid_time(valid_time) ;
		valid_time:long_name = "time" ;
		valid_time:standard_name = "time" ;
		valid_time:units = "seconds since 1970-01-01" ;
		valid_time:calendar = "proleptic_gregorian" ;
	double pressure_level(pressure_level) ;
		pressure_level:_FillValue = NaN ;
		pressure_level:long_name = "pressure" ;
		pressure_level:units = "hPa" ;
		pressure_level:positive = "down" ;
		pressure_level:stored_direction = "decreasing" ;
		pressure_level:standard_name = "air_pressure" ;
	double latitude(latitude) ;
		latitude:_FillValue = NaN ;
		latitude:units = "degrees_north" ;
		latitude:standard_name = "latitude" ;
		latitude:long_name = "latitude" ;
		latitude:stored_direction = "decreasing" ;
	double longitude(longitude) ;
		longitude:_FillValue = NaN ;
		longitude:units = "degrees_east" ;
		longitude:standard_name = "longitude" ;
		longitude:long_name = "longitude" ;
	string expver(valid_time) ;
	float t(valid_time, pressure_level, latitude, longitude) ;
		t:_FillValue = NaNf ;
		t:GRIB_paramId = 130LL ;
		t:GRIB_dataType = "an" ;
		t:GRIB_numberOfPoints = 2501LL ;
		t:GRIB_typeOfLevel = "isobaricInhPa" ;
		t:GRIB_stepUnits = 1LL ;
		t:GRIB_stepType = "instant" ;
		t:GRIB_gridType = "regular_ll" ;
		t:GRIB_uvRelativeToGrid = 0LL ;
		t:GRIB_NV = 0LL ;
		t:GRIB_Nx = 61LL ;
		t:GRIB_Ny = 41LL ;
		t:GRIB_cfName = "air_temperature" ;
		t:GRIB_cfVarName = "t" ;
		t:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		t:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		t:GRIB_iScansNegatively = 0LL ;
		t:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		t:GRIB_jPointsAreConsecutive = 0LL ;
		t:GRIB_jScansPositively = 0LL ;
		t:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		t:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		t:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		t:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		t:GRIB_missingValue = 3.40282346638529e+38 ;
		t:GRIB_name = "Temperature" ;
		t:GRIB_shortName = "t" ;
		t:GRIB_totalNumber = 0LL ;
		t:GRIB_units = "K" ;
		t:long_name = "Temperature" ;
		t:units = "K" ;
		t:standard_name = "air_temperature" ;
		t:coordinates = "number valid_time isobaricInhPa latitude longitude expver" ;
	float z(valid_time, pressure_level, latitude, longitude) ;
		z:_FillValue = NaNf ;
		z:GRIB_paramId = 129LL ;
		z:GRIB_dataType = "an" ;
		z:GRIB_numberOfPoints = 2501LL ;
		z:GRIB_typeOfLevel = "isobaricInhPa" ;
		z:GRIB_stepUnits = 1LL ;
		z:GRIB_stepType = "instant" ;
		z:GRIB_gridType = "regular_ll" ;
		z:GRIB_uvRelativeToGrid = 0LL ;
		z:GRIB_NV = 0LL ;
		z:GRIB_Nx = 61LL ;
		z:GRIB_Ny = 41LL ;
		z:GRIB_cfName = "geopotential" ;
		z:GRIB_cfVarName = "z" ;
		z:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		z:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		z:GRIB_iScansNegatively = 0LL ;
		z:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		z:GRIB_jPointsAreConsecutive = 0LL ;
		z:GRIB_jScansPositively = 0LL ;
		z:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		z:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		z:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		z:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		z:GRIB_missingValue = 3.40282346638529e+38 ;
		z:GRIB_name = "Geopotential" ;
		z:GRIB_shortName = "z" ;
		z:GRIB_totalNumber = 0LL ;
		z:GRIB_units = "m**2 s**-2" ;
		z:long_name = "Geopotential" ;
		z:units = "m**2 s**-2" ;
		z:standard_name = "geopotential" ;
		z:coordinates = "number valid_time isobaricInhPa latitude longitude expver" ;

// global attributes:
		:GRIB_centre = "ecmf" ;
		:GRIB_centreDescription = "European Centre for Medium-Range Weather Forecasts" ;
		:GRIB_subCentre = 0LL ;
		:Conventions = "CF-1.7" ;
		:institution = "European Centre for Medium-Range Weather Forecasts" ;
		:history = "2026-09-25T15:07 GRIB to CDM+CF via cfgrib-0.9.15.1/ecCodes-2.48.2 with {\"source\": \"tmpb8_h__dg/data.grib\", \"filter_by_keys\": {\"stream\": [\"oper\"], \"stepType\": [\"instant\"]}, \"encode_cf\": [\"parameter\", \"time\", \"geography\", \"vertical\"]}" ;
}
```

