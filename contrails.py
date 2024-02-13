import pandas as pd
from scipy.interpolate import griddata
import requests
from shapely.geometry import geo
import xarray as xr
import pycontrails as pc
from pycontrails.models.cocip import Cocip
from xarray.core import combine
import ecmwf
from pycontrails.models.humidity_scaling import ConstantHumidityScaling
import os
import tempfile
import json
import config


def calculate_ef_from_flight_path(flight_path):
    flight_path_df = pd.DataFrame(flight_path)

    attrs = {
        "flight_id": 123,
        "aircraft_type": config.AIRCRAFT_TYPE,
        "engine_uid": config.ENGINE_TYPE,
        "engine_efficiency": config.ENGINE_EFFICIENCY,
        "nvpm_ei_n": 1.897462e15,
        "wingspan": config.WINGSPAN,
        "n_engine": config.N_ENGINES,
    }

    flight = pc.Flight(data=flight_path_df, flight_id=123, attrs=attrs)
    params = {
        "process_emissions": False,
        "verbose_outputs": True,
        "humidity_scaling": ConstantHumidityScaling(rhi_adj=0.98),
    }
    cocip = Cocip(ecmwf.met, ecmwf.rad, params=params)
    output_flight = cocip.eval(source=flight)

    df = output_flight.dataframe
    if not df["ef"].empty:
        ef = df["ef"].sum()
    else:
        ef = 0
    # return df
    return ef, df, cocip


def interpolate_contrail_point(
    contrail_grid, point, distance
):  # Extract 4-D grid of interest
    da = contrail_grid["ef_per_m"]
    ef_per_m = da.interp(
        latitude=point[0], longitude=point[1], flight_level=point[2] / 100
    )
    return ef_per_m.sum().item() * distance


def interpolate_contrail_grid(contrail_grid, flight_path, distance):

    da = contrail_grid["ef_per_m"]

    flight_path = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft"]
    )

    fl_ds = flight_path.copy()
    fl_ds["flight_level"] = fl_ds.pop("altitude_ft") / 100
    fl_ds = xr.Dataset.from_dataframe(fl_ds)

    ef_per_m = da.interp(**fl_ds.data_vars)

    return ef_per_m.sum().item() * distance


def download_contrail_grid(altitude_grid, filename, format):
    if os.path.exists(filename):
        if format == "netcdf":
            ds_disk = xr.open_dataset(filename)
        else:
            with open(filename, "r") as f:
                ds_disk = json.load(f)

        return ds_disk

    URL = os.getenv("API_URL_BASE")
    api_key = os.getenv("API_KEY")
    headers = {"x-api-key": api_key}
    for alt in altitude_grid:
        altitude_grid[alt] = [x for x in sum(altitude_grid[alt], []) if x is not None]

    flight_path = pd.DataFrame(
        [
            (alt, *coords)
            for alt, coords_list in altitude_grid.items()
            for coords in coords_list
        ],
        columns=["altitude_ft", "latitude", "longitude"],
    )

    grid_df = pd.DataFrame(flight_path, columns=["latitude", "longitude"])
    params = {
        # Give the bbox a small buffer
        "bbox": [
            grid_df["longitude"].min() - 1,
            grid_df["latitude"].min() - 1,
            grid_df["longitude"].max() + 1,
            grid_df["latitude"].max() + 1,
        ],
        "flight_level": config.FLIGHT_LEVELS,
        "aircraft_type": config.AIRCRAFT_TYPE,
        "format": format,
    }

    ds_list = []
    time = [config.DEPARTURE_DATE, config.DEPARTURE_DATE + config.WEATHER_BOUND]
    times = pd.date_range(time[0], time[1], freq="1h")
    for t in times:
        params["time"] = str(t)
        r = requests.get(f"{URL}/grid/cocip", params=params, headers=headers)
        print(f"HTTP Response Code: {r.status_code} {r.reason}")
        # Save request to disk, open with xarray, append grid to ds_list
        if format == "netcdf":
            with tempfile.NamedTemporaryFile() as tmp, open(tmp.name, "wb") as file_obj:
                file_obj.write(r.content)
                ds = xr.load_dataset(tmp.name, engine="netcdf4", decode_timedelta=False)
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
        with open(filename, "w") as f:
            json.dump(combined_dict, f)
        ds = combined_dict
    else:
        ds = ds.to_netcdf(filename)

    return ds
