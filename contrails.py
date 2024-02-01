import pandas as pd
from scipy.interpolate import griddata
import requests
import xarray as xr
import pycontrails as pc
from pycontrails.models.cocip import Cocip
import ecmwf
from pycontrails.models.humidity_scaling import ConstantHumidityScaling
import os
import tempfile


def calculate_ef_from_flight_path(flight_path):
    flight_path_df = pd.DataFrame(flight_path)

    attrs = {
        "flight_id": 123,
        "aircraft_type": "A320",
        "engine_uid": "CFM56-5B6",
        "engine_efficiency": 0.35,
        "nvpm_ei_n": 1.897462e15,
        "wingspan": 48,
        "n_engine": 2,
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


def interpolate_contrail_grid(
    contrail_grid, flight_path
):  # Extract 4-D grid of interest
    da = contrail_grid["ef_per_m"]

    flight_path = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft"]
    )

    # Convert pd.DataFrame to xr.Dataset
    fl_ds = flight_path.copy()
    fl_ds["flight_level"] = fl_ds.pop("altitude_ft") / 100
    # here, interp_dim is the common dimension mentioned in the xarray documentation
    fl_ds = fl_ds.rename_axis("interp_dim")
    fl_ds = xr.Dataset.from_dataframe(fl_ds)

    # Run the interpolation
    ef_per_m = da.interp(**fl_ds.data_vars)

    # Convert from ef per meter to ef per waypoint
    return ef_per_m.sum()


def download_contrail_grid(routing_grid):
    if os.path.exists("contrail_grid.nc"):
        ds_disk = xr.open_dataset("contrail_grid.nc")
        return ds_disk

    URL = os.getenv("API_URL_BASE")  # https://api.contrails.org/v0
    api_key = os.getenv("API_KEY")  # put in your API key here
    headers = {"x-api-key": api_key}
    grid = sum(routing_grid, [])

    grid_df = pd.DataFrame(grid, columns=["Latitude", "Longitude"])
    params = {
        # Give the bbox a small buffer
        "bbox": [
            grid_df["Longitude"].min() - 1,
            grid_df["Latitude"].min() - 1,
            grid_df["Longitude"].max() + 1,
            grid_df["Latitude"].max() + 1,
        ],
        "aircraft_type": "A320",
    }

    ds_list = []
    time = ecmwf.time_bounds
    times = pd.date_range(time[0], time[1], freq="1H")
    for t in times:
        params["time"] = str(t)
        r = requests.get(f"{URL}/grid/cocip", params=params, headers=headers)
        print(f"HTTP Response Code: {r.status_code} {r.reason}")

        # Save request to disk, open with xarray, append grid to ds_list
        with tempfile.NamedTemporaryFile() as tmp, open(tmp.name, "wb") as file_obj:
            file_obj.write(r.content)
            ds = xr.load_dataset(tmp.name, engine="netcdf4", decode_timedelta=False)
        ds_list.append(ds)

    # Concatenate all grids into a single xr.Dataset
    ds = xr.concat(ds_list, dim="time")
    ds.to_netcdf("contrail_grid.nc")
    return ds


# TODO: Implement 4D contrail formation fields for quicker lookup
