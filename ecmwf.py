from pycontrails.models.cocip import Cocip
from pycontrails.datalib.ecmwf import ERA5


time_bounds = ("2023-03-31 00:00:00", "2023-03-31 23:00:00")
pressure_levels = (300, 250, 225, 200)
era5pl = ERA5(
    time=time_bounds,
    variables=Cocip.met_variables + Cocip.optional_met_variables,
    pressure_levels=pressure_levels,
)
era5sl = ERA5(time=time_bounds, variables=Cocip.rad_variables)
met = era5pl.open_metdataset()
rad = era5sl.open_metdataset()
