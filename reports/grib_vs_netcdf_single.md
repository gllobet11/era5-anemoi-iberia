# GRIB vs NetCDF — single 2020-01

- Ficheros: `single_2020-01.grib` (22.8 MB) vs `single_2020-01.nc.zip` (18.7 MB, 2 fichero(s) .nc)
- Dims crudas GRIB: `{'time': 744, 'latitude': 41, 'longitude': 61}` · NetCDF: `{'valid_time': 744, 'latitude': 41, 'longitude': 61}`
- Solo GRIB: [] · solo NetCDF: []
- Pasos de tiempo: GRIB 744 · NetCDF 744 · comunes 744

| Var | dtype GRIB/NC | Máx abs | units GRIB | units NC | Atributos solo en NC |
|---|---|---|---|---|---|
| msl | float32/float32 | 0 | Pa | Pa | — |
| sp | float32/float32 | 0 | Pa | Pa | — |
| t2m | float32/float32 | 0 | K | K | — |
| tp | float32/float32 | 0 | m | m | — |
| u10 | float32/float32 | 0 | m s**-1 | m s**-1 | — |
| v10 | float32/float32 | 0 | m s**-1 | m s**-1 | — |

## Cabecera NetCDF (`ncdump -h`)

```
netcdf data_stream-oper_stepType-accum {
dimensions:
	valid_time = 744 ;
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
	float tp(valid_time, latitude, longitude) ;
		tp:_FillValue = NaNf ;
		tp:GRIB_paramId = 228LL ;
		tp:GRIB_dataType = "fc" ;
		tp:GRIB_numberOfPoints = 2501LL ;
		tp:GRIB_typeOfLevel = "surface" ;
		tp:GRIB_stepUnits = 1LL ;
		tp:GRIB_stepType = "accum" ;
		tp:GRIB_gridType = "regular_ll" ;
		tp:GRIB_uvRelativeToGrid = 0LL ;
		tp:GRIB_NV = 0LL ;
		tp:GRIB_Nx = 61LL ;
		tp:GRIB_Ny = 41LL ;
		tp:GRIB_cfName = "unknown" ;
		tp:GRIB_cfVarName = "tp" ;
		tp:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		tp:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		tp:GRIB_iScansNegatively = 0LL ;
		tp:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		tp:GRIB_jPointsAreConsecutive = 0LL ;
		tp:GRIB_jScansPositively = 0LL ;
		tp:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		tp:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		tp:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		tp:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		tp:GRIB_missingValue = 3.40282346638529e+38 ;
		tp:GRIB_name = "Total precipitation" ;
		tp:GRIB_shortName = "tp" ;
		tp:GRIB_totalNumber = 0LL ;
		tp:GRIB_units = "m" ;
		tp:long_name = "Total precipitation" ;
		tp:units = "m" ;
		tp:standard_name = "unknown" ;
		tp:GRIB_surface = 0. ;
		tp:coordinates = "number valid_time latitude longitude expver" ;

// global attributes:
		:GRIB_centre = "ecmf" ;
		:GRIB_centreDescription = "European Centre for Medium-Range Weather Forecasts" ;
		:GRIB_subCentre = 0LL ;
		:Conventions = "CF-1.7" ;
		:institution = "European Centre for Medium-Range Weather Forecasts" ;
		:history = "2026-09-25T15:06 GRIB to CDM+CF via cfgrib-0.9.15.1/ecCodes-2.48.2 with {\"source\": \"tmpxc2bfeli/data.grib\", \"filter_by_keys\": {\"stream\": [\"oper\"], \"stepType\": [\"accum\"]}, \"encode_cf\": [\"parameter\", \"time\", \"geography\", \"vertical\"]}" ;
}
```

```
netcdf data_stream-oper_stepType-instant {
dimensions:
	valid_time = 744 ;
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
	float t2m(valid_time, latitude, longitude) ;
		t2m:_FillValue = NaNf ;
		t2m:GRIB_paramId = 167LL ;
		t2m:GRIB_dataType = "an" ;
		t2m:GRIB_numberOfPoints = 2501LL ;
		t2m:GRIB_typeOfLevel = "surface" ;
		t2m:GRIB_stepUnits = 1LL ;
		t2m:GRIB_stepType = "instant" ;
		t2m:GRIB_gridType = "regular_ll" ;
		t2m:GRIB_uvRelativeToGrid = 0LL ;
		t2m:GRIB_NV = 0LL ;
		t2m:GRIB_Nx = 61LL ;
		t2m:GRIB_Ny = 41LL ;
		t2m:GRIB_cfName = "unknown" ;
		t2m:GRIB_cfVarName = "t2m" ;
		t2m:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		t2m:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		t2m:GRIB_iScansNegatively = 0LL ;
		t2m:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		t2m:GRIB_jPointsAreConsecutive = 0LL ;
		t2m:GRIB_jScansPositively = 0LL ;
		t2m:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		t2m:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		t2m:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		t2m:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		t2m:GRIB_missingValue = 3.40282346638529e+38 ;
		t2m:GRIB_name = "2 metre temperature" ;
		t2m:GRIB_shortName = "2t" ;
		t2m:GRIB_totalNumber = 0LL ;
		t2m:GRIB_units = "K" ;
		t2m:long_name = "2 metre temperature" ;
		t2m:units = "K" ;
		t2m:standard_name = "unknown" ;
		t2m:GRIB_surface = 0. ;
		t2m:coordinates = "number valid_time latitude longitude expver" ;
	float u10(valid_time, latitude, longitude) ;
		u10:_FillValue = NaNf ;
		u10:GRIB_paramId = 165LL ;
		u10:GRIB_dataType = "an" ;
		u10:GRIB_numberOfPoints = 2501LL ;
		u10:GRIB_typeOfLevel = "surface" ;
		u10:GRIB_stepUnits = 1LL ;
		u10:GRIB_stepType = "instant" ;
		u10:GRIB_gridType = "regular_ll" ;
		u10:GRIB_uvRelativeToGrid = 0LL ;
		u10:GRIB_NV = 0LL ;
		u10:GRIB_Nx = 61LL ;
		u10:GRIB_Ny = 41LL ;
		u10:GRIB_cfName = "unknown" ;
		u10:GRIB_cfVarName = "u10" ;
		u10:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		u10:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		u10:GRIB_iScansNegatively = 0LL ;
		u10:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		u10:GRIB_jPointsAreConsecutive = 0LL ;
		u10:GRIB_jScansPositively = 0LL ;
		u10:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		u10:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		u10:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		u10:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		u10:GRIB_missingValue = 3.40282346638529e+38 ;
		u10:GRIB_name = "10 metre U wind component" ;
		u10:GRIB_shortName = "10u" ;
		u10:GRIB_totalNumber = 0LL ;
		u10:GRIB_units = "m s**-1" ;
		u10:long_name = "10 metre U wind component" ;
		u10:units = "m s**-1" ;
		u10:standard_name = "unknown" ;
		u10:GRIB_surface = 0. ;
		u10:coordinates = "number valid_time latitude longitude expver" ;
	float v10(valid_time, latitude, longitude) ;
		v10:_FillValue = NaNf ;
		v10:GRIB_paramId = 166LL ;
		v10:GRIB_dataType = "an" ;
		v10:GRIB_numberOfPoints = 2501LL ;
		v10:GRIB_typeOfLevel = "surface" ;
		v10:GRIB_stepUnits = 1LL ;
		v10:GRIB_stepType = "instant" ;
		v10:GRIB_gridType = "regular_ll" ;
		v10:GRIB_uvRelativeToGrid = 0LL ;
		v10:GRIB_NV = 0LL ;
		v10:GRIB_Nx = 61LL ;
		v10:GRIB_Ny = 41LL ;
		v10:GRIB_cfName = "unknown" ;
		v10:GRIB_cfVarName = "v10" ;
		v10:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		v10:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		v10:GRIB_iScansNegatively = 0LL ;
		v10:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		v10:GRIB_jPointsAreConsecutive = 0LL ;
		v10:GRIB_jScansPositively = 0LL ;
		v10:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		v10:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		v10:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		v10:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		v10:GRIB_missingValue = 3.40282346638529e+38 ;
		v10:GRIB_name = "10 metre V wind component" ;
		v10:GRIB_shortName = "10v" ;
		v10:GRIB_totalNumber = 0LL ;
		v10:GRIB_units = "m s**-1" ;
		v10:long_name = "10 metre V wind component" ;
		v10:units = "m s**-1" ;
		v10:standard_name = "unknown" ;
		v10:GRIB_surface = 0. ;
		v10:coordinates = "number valid_time latitude longitude expver" ;
	float msl(valid_time, latitude, longitude) ;
		msl:_FillValue = NaNf ;
		msl:GRIB_paramId = 151LL ;
		msl:GRIB_dataType = "an" ;
		msl:GRIB_numberOfPoints = 2501LL ;
		msl:GRIB_typeOfLevel = "surface" ;
		msl:GRIB_stepUnits = 1LL ;
		msl:GRIB_stepType = "instant" ;
		msl:GRIB_gridType = "regular_ll" ;
		msl:GRIB_uvRelativeToGrid = 0LL ;
		msl:GRIB_NV = 0LL ;
		msl:GRIB_Nx = 61LL ;
		msl:GRIB_Ny = 41LL ;
		msl:GRIB_cfName = "air_pressure_at_mean_sea_level" ;
		msl:GRIB_cfVarName = "msl" ;
		msl:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		msl:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		msl:GRIB_iScansNegatively = 0LL ;
		msl:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		msl:GRIB_jPointsAreConsecutive = 0LL ;
		msl:GRIB_jScansPositively = 0LL ;
		msl:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		msl:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		msl:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		msl:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		msl:GRIB_missingValue = 3.40282346638529e+38 ;
		msl:GRIB_name = "Mean sea level pressure" ;
		msl:GRIB_shortName = "msl" ;
		msl:GRIB_totalNumber = 0LL ;
		msl:GRIB_units = "Pa" ;
		msl:long_name = "Mean sea level pressure" ;
		msl:units = "Pa" ;
		msl:standard_name = "air_pressure_at_mean_sea_level" ;
		msl:GRIB_surface = 0. ;
		msl:coordinates = "number valid_time latitude longitude expver" ;
	float sp(valid_time, latitude, longitude) ;
		sp:_FillValue = NaNf ;
		sp:GRIB_paramId = 134LL ;
		sp:GRIB_dataType = "an" ;
		sp:GRIB_numberOfPoints = 2501LL ;
		sp:GRIB_typeOfLevel = "surface" ;
		sp:GRIB_stepUnits = 1LL ;
		sp:GRIB_stepType = "instant" ;
		sp:GRIB_gridType = "regular_ll" ;
		sp:GRIB_uvRelativeToGrid = 0LL ;
		sp:GRIB_NV = 0LL ;
		sp:GRIB_Nx = 61LL ;
		sp:GRIB_Ny = 41LL ;
		sp:GRIB_cfName = "surface_air_pressure" ;
		sp:GRIB_cfVarName = "sp" ;
		sp:GRIB_gridDefinitionDescription = "Latitude/Longitude Grid" ;
		sp:GRIB_iDirectionIncrementInDegrees = 0.25 ;
		sp:GRIB_iScansNegatively = 0LL ;
		sp:GRIB_jDirectionIncrementInDegrees = 0.25 ;
		sp:GRIB_jPointsAreConsecutive = 0LL ;
		sp:GRIB_jScansPositively = 0LL ;
		sp:GRIB_latitudeOfFirstGridPointInDegrees = 45. ;
		sp:GRIB_latitudeOfLastGridPointInDegrees = 35. ;
		sp:GRIB_longitudeOfFirstGridPointInDegrees = -10. ;
		sp:GRIB_longitudeOfLastGridPointInDegrees = 5. ;
		sp:GRIB_missingValue = 3.40282346638529e+38 ;
		sp:GRIB_name = "Surface pressure" ;
		sp:GRIB_shortName = "sp" ;
		sp:GRIB_totalNumber = 0LL ;
		sp:GRIB_units = "Pa" ;
		sp:long_name = "Surface pressure" ;
		sp:units = "Pa" ;
		sp:standard_name = "surface_air_pressure" ;
		sp:GRIB_surface = 0. ;
		sp:coordinates = "number valid_time latitude longitude expver" ;

// global attributes:
		:GRIB_centre = "ecmf" ;
		:GRIB_centreDescription = "European Centre for Medium-Range Weather Forecasts" ;
		:GRIB_subCentre = 0LL ;
		:Conventions = "CF-1.7" ;
		:institution = "European Centre for Medium-Range Weather Forecasts" ;
		:history = "2026-09-25T15:06 GRIB to CDM+CF via cfgrib-0.9.15.1/ecCodes-2.48.2 with {\"source\": \"tmpxc2bfeli/data.grib\", \"filter_by_keys\": {\"stream\": [\"oper\"], \"stepType\": [\"instant\"]}, \"encode_cf\": [\"parameter\", \"time\", \"geography\", \"vertical\"]}" ;
}
```

