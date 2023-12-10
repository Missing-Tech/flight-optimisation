import os
from pycontrails.models.cocip import Cocip
from pycontrails.datalib.ecmwf import ERA5
import util
import pandas as pd
import xarray as xr

time_bounds = ("2023-03-31 23:00:00", "2023-04-01 11:00:00")
pressure_levels = (300, 250, 200)
era5pl = ERA5(
    time=time_bounds,
    timestep_freq="1H",
    variables=Cocip.met_variables + Cocip.optional_met_variables,
    pressure_levels=pressure_levels,
)
era5sl = ERA5(time=time_bounds, variables=Cocip.rad_variables)
met = era5pl.open_metdataset()
rad = era5sl.open_metdataset()


class MetAltitudeGrid:
    def __init__(self, routing_grid):
        self.flight_path = routing_grid
        self.weather_data = self.init_weather_data_along_path(routing_grid)

    def init_weather_data_along_path(self, routing_grid):
        if not os.path.exists("weather_data.nc"):
            df = pd.DataFrame(
                sum(routing_grid[30000], []), columns=["latitude", "longitude"]
            )
            lat = df["latitude"]
            lon = df["longitude"]
            weather_data = met.data.sel(
                latitude=slice(lat.min(), lat.max()),
                longitude=slice(lon.min(), lon.max()),
            ).to_netcdf("weather_data.nc")

        weather_data = xr.open_dataset("weather_data.nc")

        return weather_data

    def get_weather_data_at_point(self, point, pressure):
        data = self.weather_data.sel(
            latitude=point["latitude"],
            longitude=point["longitude"],
            level=pressure,
            method="nearest",
        )
        return data.isel(time=0)

    def get_wind_vector_at_point(self, point):
        nearest_pressure = get_nearest_pressure_level_at_point(point)
        data = self.get_weather_data_at_point(point, nearest_pressure)
        u = data["eastward_wind"].values
        v = data["northward_wind"].values

        return (u, v)

    def get_temperature_at_point(self, point):
        nearest_pressure = get_nearest_pressure_level_at_point(point)
        temperature = self.get_weather_data_at_point(point, nearest_pressure)[
            "air_temperature"
        ].values
        return temperature


def get_wind_vectors_at_hpa(pressure_level_hpa):
    wind_data = met.data.sel(level=pressure_level_hpa)
    wind_data = wind_data.to_dataframe()[["northward_wind", "eastward_wind"]]
    return wind_data


def get_nearest_pressure_level_at_point(point):
    pressure = util.calculate_pressure_from_altitude_ft(point["altitude_ft"])
    nearest_pressure = util.get_nearest_value_from_list(pressure, pressure_levels)
    return nearest_pressure
