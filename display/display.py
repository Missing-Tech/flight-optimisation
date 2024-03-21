from matplotlib.collections import LineCollection, PolyCollection
import config
import shapely
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from cartopy import crs as ccrs
from cartopy.feature import BORDERS, COASTLINE
from cartopy.mpl.patch import geos_to_path
import itertools
import numpy as np
import json
from matplotlib.animation import FuncAnimation

crs = ccrs.NearsidePerspective(central_latitude=51, central_longitude=-35)
crs_proj4 = crs.proj4_init

wgs84 = "WGS84"


def create_3d_flight_frame(
    timestep, flight_path, contrail_grid, contrail_polys, line, ax=None
):
    long = flight_path["longitude"][:timestep]
    lat = flight_path["latitude"][:timestep]
    alt = flight_path["altitude_ft"][:timestep]
    ax.set_title(f"Flight Path at Timestep {flight_path['time'][timestep]}")
    line.set_xdata(long)
    line.set_ydata(lat)
    line.set_3d_properties(alt)
    timestamps = contrail_grid["time"]

    # Interpolate contrail grid data at the given timestamp
    nearest_timestamp_index = np.argmin(
        np.abs(timestamps - np.datetime64(flight_path["time"][timestep])).values
    )
    time = convert_time_string(contrail_grid["time"][nearest_timestamp_index].values)
    polys = get_contrail_polys_at_time(contrail_polys, time)
    for col in ax.collections:
        if isinstance(col, PolyCollection):
            col.remove()
    for level in polys:
        ax.add_collection3d(polys[level], zs=level * 100, zdir="z")

    return line


def get_contrail_polys_at_time(contrail_polys, time):
    collections = {}
    polys = contrail_polys["polys"]
    for level in config.FLIGHT_LEVELS:
        patches = []
        for poly in polys:
            if (
                poly["properties"]["level"] == level
                and poly["properties"]["time"] == time
            ):
                multipoly = shapely.from_geojson(json.dumps(poly))
                for geom in multipoly.geoms:
                    geom = geom.simplify(0.1)
                    x, y = geom.exterior.coords.xy
                    patches.append(np.asarray(tuple(zip(x, y))))
        collection = PolyCollection(patches, facecolor="red", alpha=0.5)
        collections[level] = collection

    return collections


def convert_time_string(time):
    new_time_str = np.datetime_as_string(time, unit="s") + "Z"
    return new_time_str


def create_3d_flight_animation(
    flight_path,
    contrail_grid,
    contrail_polys,
    fig=None,
    ax=None,
    interval=200,
):
    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft", "time"]
    )
    line = ax.plot(
        flight_path_df["longitude"][0],
        flight_path_df["latitude"][0],
        flight_path_df["altitude_ft"][0],
        color="b",
    )[0]

    time = convert_time_string(contrail_grid["time"][0].values)
    polys = get_contrail_polys_at_time(contrail_polys, time)
    for level in polys:
        ax.add_collection3d(polys[level], zs=level * 100, zdir="z")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_zlabel("Altitude")
    ani = FuncAnimation(
        fig,
        create_3d_flight_frame,
        frames=len(flight_path),
        interval=interval,
        fargs=(flight_path_df, contrail_grid, contrail_polys, line, ax),
        blit=False,
    )
    return ani


def create_flight_frame(hours, flight_path, contrail_grid, line, grid, title, ax=None):
    time = flight_path["time"].iloc[0] + pd.Timedelta(hours=hours * 2)

    flight_path_before_time = flight_path[flight_path["time"] <= time]

    lon = flight_path_before_time["longitude"]
    lat = flight_path_before_time["latitude"]

    ax.set_title(
        f"{title} at Timestep {time.strftime('%H:%M')}, Altitude: {flight_path_before_time['altitude_ft'].iloc[-1]} ft"
    )
    line.set_xdata(lon)
    line.set_ydata(lat)
    timestamps = contrail_grid["time"]

    # Interpolate contrail grid data at the given timestamp
    nearest_timestamp_index = np.argmin(np.abs(timestamps - np.datetime64(time)).values)

    nearest_flight_level_index = np.argmin(
        np.abs(
            config.FLIGHT_LEVELS
            - (flight_path_before_time["altitude_ft"].iloc[-1] / 100)
        )
    )
    interpolated_grid = contrail_grid.isel(
        flight_level=nearest_flight_level_index, time=nearest_timestamp_index
    )

    transposed = interpolated_grid["ef_per_m"].transpose().values
    grid.set_array(transposed.ravel())
    return line, grid


def create_flight_animation(
    flight_path,
    contrail_grid,
    title="Flight path",
    fig=None,
    ax=None,
    interval=1000,
):
    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "time", "altitude_ft"]
    )
    line = ax.plot(
        flight_path_df["longitude"][0],
        flight_path_df["latitude"][0],
        transform=ccrs.PlateCarree(),
        color="b",
    )[0]
    contrail_data = contrail_grid.isel(flight_level=4, time=0)
    grid = ax.pcolormesh(
        contrail_data["longitude"],
        contrail_data["latitude"],
        contrail_data["ef_per_m"].transpose(),
        shading="gourard",
        vmin=-1e9,
        vmax=1e9,
        cmap="coolwarm",
        transform=ccrs.PlateCarree(),
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ani = FuncAnimation(
        fig,
        create_flight_frame,
        frames=5,
        interval=interval,
        fargs=(flight_path_df, contrail_grid, line, grid, title, ax),
        blit=False,
    )
    return ani


def create_aco_frame(index, paths, line, ax, best_indexes, best_path):
    flight_path = paths[index]
    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "time", "altitude_ft"]
    )
    lon = flight_path_df["longitude"]
    lat = flight_path_df["latitude"]
    line.set_xdata(lon)
    line.set_ydata(lat)

    if index in best_indexes:
        best_path_df = pd.DataFrame(
            best_indexes[index],
            columns=["latitude", "longitude", "time", "altitude_ft"],
        )
        best_path.set_xdata(best_path_df["longitude"])
        best_path.set_ydata(best_path_df["latitude"])

    ax.set_title(f"Path #{index}")

    return line, best_path


def create_aco_animation(
    paths,
    best_indexes,
    fig=None,
    ax=None,
    interval=100,
):
    flight_path_df = pd.DataFrame(
        paths[0], columns=["latitude", "longitude", "time", "altitude_ft"]
    )
    line = ax.plot(
        flight_path_df["longitude"],
        flight_path_df["latitude"],
        transform=ccrs.PlateCarree(),
        c="k",
        alpha=0.5,
        linewidth=0.5,
    )[0]

    best_path_df = pd.DataFrame(
        best_indexes[0], columns=["latitude", "longitude", "time", "altitude_ft"]
    )
    best_path = ax.plot(
        best_path_df["longitude"],
        best_path_df["latitude"],
        transform=ccrs.PlateCarree(),
        c="r",
    )[0]

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ani = FuncAnimation(
        fig,
        create_aco_frame,
        frames=len(paths),
        interval=interval,
        fargs=(paths, line, ax, best_indexes, best_path),
        blit=False,
    )
    return ani
