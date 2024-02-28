import os
import numpy as np
import time
from pandas._libs.tslibs import np_datetime
from pycontrails.models.cocip import Cocip
from pycontrails.datalib.ecmwf import ERA5
import util
import pandas as pd
import xarray as xr
import config


time_bounds = (config.DEPARTURE_DATE, config.DEPARTURE_DATE + config.WEATHER_BOUND)
pressure_levels = config.PRESSURE_LEVELS
era5pl = ERA5(
    time=time_bounds,
    timestep_freq="1h",
    variables=Cocip.met_variables + Cocip.optional_met_variables,
    pressure_levels=pressure_levels,
)
era5sl = ERA5(time=time_bounds, variables=Cocip.rad_variables)
met = era5pl.open_metdataset()
rad = era5sl.open_metdataset()


class MetAltitudeGrid:
    def __init__(self, altitude_grid):
        self.flight_path = altitude_grid
        self.weather_data = self.init_weather_data_along_grid(altitude_grid)

    def init_weather_data_along_grid(self, altitude_grid):
        if not os.path.exists("data/weather_data.nc"):

            for alt in altitude_grid:
                altitude_grid[alt] = [
                    x for x in sum(altitude_grid[alt], []) if x is not None
                ]

            flight_path = pd.DataFrame(
                [
                    (alt, *coords)
                    for alt, coords_list in altitude_grid.items()
                    for coords in coords_list
                ],
                columns=["altitude_ft", "latitude", "longitude"],
            )

            fl_ds = flight_path.copy()
            fl_ds = fl_ds.set_index(["altitude_ft", "latitude", "longitude"])
            fl_ds = xr.Dataset.from_dataframe(fl_ds)
            weather = met.data.interp(**fl_ds.data_vars)

            weather.to_netcdf("data/weather_data.nc")

        weather_data = xr.open_dataset("data/weather_data.nc")

        return weather_data

    def get_weather_data_at_point(self, point):
        data = self.weather_data.sel(
            latitude=point["latitude"],
            longitude=point["longitude"],
            time=point["time"],
            level=point["level"],
            method="nearest",
        )
        return data

    def get_wind_vector_at_point(self, point):
        u = point["eastward_wind"].values
        v = point["northward_wind"].values

        return (u, v)

    def get_temperature_at_point(self, point):
        temperature = point["air_temperature"].values
        return temperature


def get_wind_vectors_at_hpa(pressure_level_hpa):
    wind_data = met.data.sel(level=pressure_level_hpa)
    wind_data = wind_data.to_dataframe()[["northward_wind", "eastward_wind"]]
    return wind_data


def get_nearest_pressure_level_at_point(point):
    pressure = util.calculate_pressure_from_altitude_ft(point["altitude_ft"])
    nearest_pressure = util.get_nearest_value_from_list(pressure, pressure_levels)
    return nearest_pressure
