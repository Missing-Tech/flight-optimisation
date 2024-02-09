import os
import pycontrails as ct
from pycontrails.models.cocip import Cocip
from pycontrails.datalib.ecmwf import ERA5
import util
import time
import pandas as pd
import xarray as xr
import config
import cdsapi


time_bounds = (config.DEPARTURE_DATE, config.DEPARTURE_DATE + config.WEATHER_BOUND)
pressure_levels = config.PRESSURE_LEVELS
era5pl = ERA5(
    time=time_bounds,
    timestep_freq="1h",
    variables=Cocip.met_variables + Cocip.optional_met_variables,
    pressure_levels=pressure_levels,
    # area=[
    #     56.8,
    #     -91.2,
    #     21.9,
    #     19.5,
    # ],
)
era5sl = ERA5(time=time_bounds, variables=Cocip.rad_variables)
met = era5pl.open_metdataset()
rad = era5sl.open_metdataset()
# weather = xr.open_dataset("weather_data.nc")
# print(weather["time"])
# met = era5pl._process_dataset(weather)
# radiation = xr.open_dataset("radiation.nc")
# rad = era5sl._preprocess_era5_dataset(radiation)
# rad = era5sl._process_dataset(rad)


class MetAltitudeGrid:
    def __init__(self, routing_grid):
        self.flight_path = routing_grid
        self.weather_data = self.init_weather_data_along_path(routing_grid)

    def init_weather_data_along_path(self, routing_grid):
        if not os.path.exists("weather_data.nc"):

            for alt in routing_grid:
                routing_grid[alt] = [
                    x for x in sum(routing_grid[alt], []) if x is not None
                ]

            flight_path = pd.DataFrame(
                [
                    (alt, *coords)
                    for alt, coords_list in routing_grid.items()
                    for coords in coords_list
                ],
                columns=["altitude_ft", "latitude", "longitude"],
            )

            fl_ds = flight_path.copy()
            fl_ds = fl_ds.set_index(["altitude_ft", "latitude", "longitude"])
            # fl_ds["level"] = util.calculate_pressure_from_altitude_ft(
            #     fl_ds.pop("altitude_ft")
            # )
            fl_ds = xr.Dataset.from_dataframe(fl_ds)
            weather = met.data.interp(**fl_ds.data_vars)

            weather.to_netcdf("weather_data.nc")

        weather_data = xr.open_dataset("weather_data.nc")

        return weather_data

    def get_weather_data_at_point(self, point, pressure):
        data = self.weather_data.sel(
            latitude=point["latitude"],
            longitude=point["longitude"],
            time=point["time"],
            level=pressure,
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
