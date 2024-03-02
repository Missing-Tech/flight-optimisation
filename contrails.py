import openap
import pandas as pd
from pycontrails.core import flight
import geodesic_path as gp
import altitude_grid as ag
import requests
import xarray as xr
import pycontrails as pc
from pycontrails.models.cocip import Cocip
import ecmwf
from pycontrails.models.humidity_scaling import ConstantHumidityScaling
import os
import tempfile
import json
import config
from pycontrails.models.ps_model import PSGrid
import util


def get_ps_grid():
    if os.path.exists("data/ps_grid.nc"):
        return xr.open_dataset("data/ps_grid.nc")
    else:
        ps_grid = PSGrid(ecmwf.met, aircraft_type=config.AIRCRAFT_TYPE).eval()
        ps_grid.data.to_netcdf("data/ps_grid.nc")
        return xr.open_dataset("data/ps_grid.nc")


ps_grid = get_ps_grid()


def get_performance_data_at_point(point):
    level = util.calculate_pressure_from_altitude_ft(point["altitude_ft"])
    level = max(min(level, config.PRESSURE_LEVELS[0]), config.PRESSURE_LEVELS[-1])

    performance_data = ps_grid.interp(
        latitude=point["latitude"],
        longitude=point["longitude"],
        level=level,
        time=point["time"],
    )

    return performance_data


def calculate_ef_from_flight_path(flight_path):
    flight_path_df = pd.DataFrame(flight_path)

    attrs = {
        "flight_id": 123,
        "aircraft_type": config.AIRCRAFT_TYPE,
        "wingspan": config.WINGSPAN,
        "nvpm_ei_n": 1.897264e15,
        "n_engine": config.N_ENGINES,
    }

    flight = pc.Flight(data=flight_path_df, flight_id=123, attrs=attrs)
    params = {
        "process_emissions": False,
        "radiative_heating_effects": True,
        "humidity_scaling": ConstantHumidityScaling(rhi_adj=0.98),
    }
    cocip = Cocip(ecmwf.met, ecmwf.rad, params=params)
    output_flight = cocip.eval(source=flight)

    df = output_flight.dataframe
    if not df["ef"].empty:
        ef = df["ef"].sum()
    else:
        ef = 0

    return ef, df, cocip


def interpolate_contrail_point(
    contrail_grid,
    point,
):  # Extract 4-D grid of interest
    da = contrail_grid["ef_per_m"]
    ef_per_m = da.interp(
        latitude=point[0], longitude=point[1], flight_level=point[2] / 100
    )
    distance = gp.calculate_step_between_airports()
    return ef_per_m.sum().item() * distance * 1000


def interpolate_contrail_grid(
    contrail_grid,
    flight_path,
):

    da = contrail_grid["ef_per_m"]

    flight_path = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft"]
    )

    fl_ds = flight_path.copy()
    fl_ds["flight_level"] = fl_ds.pop("altitude_ft") / 100
    fl_ds = xr.Dataset.from_dataframe(fl_ds)

    ef_per_m = da.interp(**fl_ds.data_vars)

    distance = gp.calculate_step_between_airports()
    return ef_per_m.sum().item() * distance * 1000


def get_contrail_grid():
    if os.path.exists("data/contrail_grid.nc"):
        return xr.open_dataset("data/contrail_grid.nc")
    else:
        contrail_grid = download_contrail_grid(ag.get_altitude_grid(), "netcdf")
        ds = contrail_grid.to_netcdf("data/contrail_grid.nc")
        return ds


def get_contrail_polys():
    if os.path.exists("data/contrail_polys.json"):
        with open("data/contrail_polys.json", "r") as f:
            return json.load(f)
    else:
        contrail_polys = download_contrail_grid(ag.get_altitude_grid(), "geojson")
        with open("data/contrail_polys.json", "w") as f:
            json.dump(contrail_polys, f)
        return contrail_polys


def download_contrail_grid(altitude_grid, format):
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
        "bbox": [
            grid_df["longitude"].min() - 1,
            grid_df["latitude"].min() - 1,
            grid_df["longitude"].max() + 1,
            grid_df["latitude"].max() + 1,
        ],
        "flight_level": config.FLIGHT_LEVELS,
        "aircraft_type": "B737",
        "format": format,
    }

    ds_list = []
    timerange = [config.DEPARTURE_DATE, config.DEPARTURE_DATE + config.WEATHER_BOUND]
    times = pd.date_range(timerange[0], timerange[1], freq="1h")
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
        ds = combined_dict

    return ds
