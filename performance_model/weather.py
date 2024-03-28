import os
from pycontrails.models.cocip import Cocip
from pycontrails.datalib.ecmwf import ERA5
from pycontrails.core.met import MetDataset
import pandas as pd
import xarray as xr

from config import Config
from routing_graph import AltitudeGrid
from _types import FlightPoint, WindVector


class WeatherGrid:
    def __init__(self, altitude_grid: AltitudeGrid, config: Config):
        """
        Class to interpolate weather data along the routing grid
        """
        self.config: Config = config
        self.met: MetDataset = self._get_met()
        self.rad: MetDataset = self._get_rad()
        self.altitude_grid: AltitudeGrid = altitude_grid
        time_bounds = (
            self.config.DEPARTURE_DATE,
            self.config.DEPARTURE_DATE + self.config.WEATHER_BOUND,
        )
        pressure_levels = self.config.PRESSURE_LEVELS
        self.era5pl: ERA5 = ERA5(
            time=time_bounds,
            timestep_freq="1h",
            variables=Cocip.met_variables + Cocip.optional_met_variables,
            pressure_levels=pressure_levels,
        )
        self.era5sl: ERA5 = ERA5(time=time_bounds, variables=Cocip.rad_variables)

    def get_weather_grid(self) -> xr.Dataset:
        """
        Gets the weather data along the grid
        """
        self.weather_grid: xr.Dataset = self._init_weather_data_along_grid(
            self.altitude_grid
        )
        return self.weather_grid

    def _get_met(self) -> MetDataset:
        """
        Retrieves the met dataset, or creates it if it doesn't exist
        """
        if not os.path.exists("data/met.nc"):
            met = self.era5pl.open_metdataset()

            met.data.to_netcdf("data/met.nc")
        else:
            met = xr.open_dataset("data/met.nc")
            met = MetDataset(met)

        return met

    def _get_rad(self) -> MetDataset:
        """
        Retrieves the met dataset, or creates it if it doesn't exist
        """
        if not os.path.exists("data/rad.nc"):
            rad = self.era5sl.open_metdataset()
            rad.data.to_netcdf("data/rad.nc")
        else:
            rad = xr.open_dataset("data/rad.nc")
            rad = MetDataset(rad)

        return rad

    def _init_weather_data_along_grid(self, grid: AltitudeGrid) -> xr.Dataset:
        """
        Initializes the weather data along the grid
        """
        if not os.path.exists("data/weather_data.nc"):
            for alt in grid:
                grid[alt] = [x for x in sum(grid[alt], []) if x is not None]

            flight_path = pd.DataFrame(
                [
                    (alt, *coords)
                    for alt, coords_list in grid.items()
                    for coords in coords_list
                ],
                columns=["altitude_ft", "latitude", "longitude"],
            )

            fl_ds = flight_path.copy()
            fl_ds = fl_ds.set_index(["altitude_ft", "latitude", "longitude"])
            fl_ds = xr.Dataset.from_dataframe(fl_ds)
            weather = self.met.data.interp(**fl_ds.data_vars)

            weather.to_netcdf("data/weather_data.nc")

        weather_data = xr.open_dataset("data/weather_data.nc")

        return weather_data

    def get_weather_data_at_point(self, point: FlightPoint) -> xr.Dataset:
        """
        Gets the weather data at a point in the grid
        """
        data = self.weather_grid.sel(
            latitude=point["latitude"],
            longitude=point["longitude"],
            time=point["time"],
            level=point["level"],
            method="nearest",
        )
        return data

    def get_wind_vector_at_point(self, point: xr.Dataset) -> WindVector:
        """
        Gets the wind vector at a point and returns it as a tuple
        """
        u = point["eastward_wind"].values
        v = point["northward_wind"].values

        return WindVector(u, v)

    def get_temperature_at_point(self, point: xr.Dataset) -> float:
        """
        Gets the temperature at a point and returns it
        """
        temperature = point["air_temperature"].values
        return temperature
