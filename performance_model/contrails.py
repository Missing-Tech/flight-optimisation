import pandas as pd
import requests
import xarray as xr
import pycontrails as pc
from pycontrails.models.cocip import Cocip
from pycontrails.models.humidity_scaling import ConstantHumidityScaling
import os
import tempfile
import json


class CocipManager:
    def __init__(self, weather_grid, config):
        self.config = config
        self.met = weather_grid.met
        self.rad = weather_grid.rad

    def calculate_ef_from_flight_path(self, flight_path):
        flight_path_df = pd.DataFrame(flight_path)

        attrs = {
            "flight_id": 123,
            "aircraft_type": self.config.AIRCRAFT_TYPE,
            "wingspan": self.config.WINGSPAN,
            "nvpm_ei_n": 1.897264e15,
            "n_engine": self.config.N_ENGINES,
        }

        flight = pc.Flight(data=flight_path_df, flight_id=123, attrs=attrs)
        params = {
            "process_emissions": False,
            "radiative_heating_effects": True,
            "humidity_scaling": ConstantHumidityScaling(rhi_adj=0.98),
        }
        cocip = Cocip(self.met, self.rad, params=params)
        output_flight = cocip.eval(source=flight)

        df = output_flight.dataframe
        if not df["ef"].empty:
            ef = df["ef"].sum()
        else:
            ef = 0

        return ef, df, cocip


class ContrailGrid:
    def __init__(self, contrail_grid):
        self.contrail_grid = contrail_grid

    def interpolate_contrail_point(
        self,
        point,
    ):  # Extract 4-D grid of interest
        da = self.contrail_grid["ef_per_m"]
        ef_per_m = da.interp(
            latitude=point[0], longitude=point[1], flight_level=point[2] / 100
        )
        return ef_per_m.sum().item()

    def interpolate_contrail_grid(
        self,
        grid,
    ):
        da = self.contrail_grid["ef_per_m"]

        flight_path = pd.DataFrame(
            grid, columns=["latitude", "longitude", "altitude_ft"]
        )

        fl_ds = flight_path.copy()
        fl_ds["flight_level"] = fl_ds.pop("altitude_ft") / 100
        fl_ds = xr.Dataset.from_dataframe(fl_ds)

        ef_per_m = da.interp(**fl_ds.data_vars)

        return ef_per_m.sum().item()


class ContrailGridManager:
    def __init__(self, altitude_grid, config):
        self.config = config
        self.contrail_polys = self._get_contrail_polys()
        self.altitude_grid = altitude_grid
        self.contrail_grid = ContrailGrid(self._get_contrail_grid())

    def _get_contrail_grid(self):
        if os.path.exists("data/contrail_grid.nc"):
            return xr.open_dataset("data/contrail_grid.nc")
        else:
            contrail_grid = self._download_contrail_grid()
            contrail_grid.to_netcdf("data/contrail_grid.nc")
            return contrail_grid

    def _get_contrail_polys(self):
        if os.path.exists("data/contrail_polys.json"):
            with open("data/contrail_polys.json", "r") as f:
                return json.load(f)
        else:
            contrail_polys = self._download_contrail_grid(format="geojson")
            with open("data/contrail_polys.json", "w") as f:
                json.dump(contrail_polys, f)
            return contrail_polys

    def _download_contrail_grid(self, format="netcdf"):
        URL = os.getenv("API_URL_BASE")
        api_key = os.getenv("API_KEY")
        headers = {"x-api-key": api_key}

        flight_path = pd.DataFrame(
            [
                (alt, *coords)
                for alt, coords_list in self.altitude_grid.items()
                for coords in coords_list
            ],
            columns=["altitude_ft", "latitude", "longitude"],
        )

        grid_df = pd.DataFrame(flight_path, columns=["latitude", "longitude"])
        params = {
            "bbox": [
                grid_df["longitude"].min() - 1,
                grid_df["latitude"].min() - 1,
                grid_df["longitude"].max() + 1,
                grid_df["latitude"].max() + 1,
            ],
            "flight_level": self.config.FLIGHT_LEVELS,
            "aircraft_type": "B737",
            "format": format,
        }

        ds_list = []
        timerange = [
            self.config.DEPARTURE_DATE,
            self.config.DEPARTURE_DATE + self.config.WEATHER_BOUND,
        ]
        times = pd.date_range(timerange[0], timerange[1], freq="1h")
        for t in times:
            params["time"] = str(t)
            r = requests.get(f"{URL}/grid/cocip", params=params, headers=headers)
            print(f"HTTP Response Code: {r.status_code} {r.reason}")
            # Save request to disk, open with xarray, append grid to ds_list
            if format == "netcdf":
                with tempfile.NamedTemporaryFile() as tmp, open(
                    tmp.name, "wb"
                ) as file_obj:
                    file_obj.write(r.content)
                    ds = xr.load_dataset(
                        tmp.name, engine="netcdf4", decode_timedelta=False
                    )
                ds_list.append(ds)
            else:
                geojson = r.json()
                for feature in geojson["features"]:
                    for coords in feature["geometry"]["coordinates"]:
                        for poly in coords:
                            for point in poly:
                                del point[2]
                    ds_list.append(feature)

        # Concatenate all grids into a single xr.Dataset
        if format == "netcdf":
            ds = xr.concat(ds_list, dim="time")
        if format == "geojson":
            combined_dict = {"polys": ds_list}
            ds = combined_dict

        return ds
