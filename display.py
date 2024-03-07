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


def create_map_ax(fig=None):
    if fig is None:
        fig = plt.figure()
    ax = fig.add_subplot(111, projection=crs)
    ax.set_extent([10, -90, 25, 60])
    ax.add_feature(BORDERS, lw=0.5, color="gray")
    ax.gridlines(draw_labels=True, color="gray", alpha=0.5, ls="--")
    ax.coastlines(resolution="50m", lw=0.5, color="gray")
    return fig, ax


def create_side_by_side_ax(fig=None):
    if fig is None:
        fig = plt.figure(figsize=(10, 5))

    # Define projection
    # crs = ccrs.PlateCarree()
    #
    # Create first subplot
    ax1 = fig.add_subplot(121, projection=crs)
    ax1.set_extent([10, -90, 25, 60])
    ax1.add_feature(BORDERS, lw=0.5, color="gray")
    ax1.gridlines(draw_labels=True, color="gray", alpha=0.5, linestyle="--")
    ax1.coastlines(resolution="50m", lw=0.5, color="gray")

    # Create second subplot
    ax2 = fig.add_subplot(122, projection=crs)
    ax2.set_extent([10, -90, 25, 60])
    ax2.add_feature(BORDERS, lw=0.5, color="gray")
    ax2.gridlines(draw_labels=True, color="gray", alpha=0.5, linestyle="--")
    ax2.coastlines(resolution="50m", lw=0.5, color="gray")

    return fig, ax1, ax2


def create_blank_ax(fig=None):
    if fig is None:
        fig = plt.figure()
    ax = fig.add_subplot(111)
    return fig, ax


def create_3d_ax(fig=None):
    if fig is None:
        fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    lc = extract_map_geometry()
    ax.add_collection3d(lc, zs=28_000, zdir="z")

    ax.set_zlim(30000, 40000)

    return fig, ax


def display_objective_over_iterations(objectives, ax=None):
    ax2 = ax.twinx()
    ax3 = ax.twinx()
    p1 = ax.plot(objectives["co2"], label="CO2", color="r")
    p2 = ax2.plot(objectives["contrail"], label="Contrail", color="b")
    p3 = ax3.plot(objectives["time"], label="Time", color="g")

    ax.set_ylabel("CO2 EF")
    ax2.set_ylabel("Contrail EF")
    ax3.set_ylabel("Time (hours)")

    ax.yaxis.label.set_color(p1[0].get_color())
    ax2.yaxis.label.set_color(p2[0].get_color())
    ax3.yaxis.label.set_color(p3[0].get_color())

    ax.set_xlabel("Iteration")
    ax.set_title("Objective over iterations")
    ax.legend(handles=p1 + p2 + p3, loc="best")
    ax3.spines["right"].set_position(("outward", 60))


def display_flight_ef(flight_path_cocip, ax=None):
    if flight_path_cocip.contrail is None:
        return

    flight_path_cocip.contrail.plot.scatter(
        "longitude",
        "latitude",
        c="ef",
        vmin=-1e12,
        vmax=1e12,
        transform=ccrs.PlateCarree(),
        cmap="coolwarm",
        ax=ax,
    )


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


def display_wind_vectors(wind_data, ax=None):
    wind_data = wind_data.isel(time=0, level=2)

    u = wind_data["eastward_wind"]
    v = wind_data["northward_wind"]

    ax.streamplot(
        u.longitude,
        u.latitude,
        u.values.T,
        v.values.T,
        linewidth=0.5,
        density=1,
        color="silver",
        transform=ccrs.PlateCarree(),
    )


def display_contrail_grid(contrail_grid, ax=None):
    contrail_grid.isel(flight_level=4, time=0).plot(
        x="longitude",
        y="latitude",
        vmin=-2e8,
        vmax=2e8,
        cmap="coolwarm",
        ax=ax,
        transform=ccrs.PlateCarree(),
    )


def display_flight_altitude(flight_path, ax=None, color="k"):
    if ax is None:
        _, ax = create_blank_ax()

    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft", "time"]
    )
    ax.plot(
        flight_path_df["time"], flight_path_df["altitude_ft"], color=color, linewidth=1
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Altitude (ft)")
    ax.set_title("Flight Altitude")


def display_flight_path(flight_path, ax=None, linewidth=0.5):
    if ax is None:
        _, ax = create_map_ax()
    flight_path_df = pd.DataFrame(flight_path, columns=["latitude", "longitude"])

    ax.plot(
        flight_path_df["longitude"],
        flight_path_df["latitude"],
        color="k",
        linewidth=linewidth,
        transform=ccrs.PlateCarree(),
    )


def display_geodesic_path(points, ax=None):
    if ax is None:
        _, ax = create_map_ax()
    geodesic_path_df = pd.DataFrame(
        points, columns=["Latitude", "Longitude", "Azimuth"]
    )
    ax.plot(
        geodesic_path_df["Longitude"],
        geodesic_path_df["Latitude"],
        transform=ccrs.PlateCarree(),
        color="green",
        linestyle="dashed",
        linewidth=1,
    )


def display_routing_grid(grid, ax=None):
    grid = sum(grid, [])

    routing_grid_df = pd.DataFrame(grid, columns=["Latitude", "Longitude"])

    ax.scatter(
        routing_grid_df["Longitude"],
        routing_grid_df["Latitude"],
        transform=ccrs.PlateCarree(),
        color="blue",
        s=0.2,
    )


def extract_map_geometry():
    coastline_geoms = COASTLINE.geometries()

    target_projection = ccrs.PlateCarree()
    geoms = [
        target_projection.project_geometry(geom, COASTLINE.crs)
        for geom in coastline_geoms
    ]
    paths = list(itertools.chain.from_iterable(geos_to_path(geom) for geom in geoms))

    segments = []
    for path in paths:
        vertices = [vertex for vertex, _ in path.iter_segments()]
        vertices = np.asarray(vertices)
        segments.append(vertices)

    lc = LineCollection(segments, color="black", linewidth=0.5)
    return lc


# Function to display altitude grid as 3D scatter plot
# Method from https://stackoverflow.com/questions/23785408/3d-cartopy-similar-to-matplotlib-basemap
def display_altitude_grid_3d(grid, ax=None):
    lc = extract_map_geometry()
    ax.add_collection3d(lc, zs=28_000, zdir="z")

    for alt in grid:
        grid[alt] = [x for x in sum(grid[alt], []) if x is not None]

    altitude_grid_df = pd.DataFrame(
        [(alt, *coords) for alt, coords_list in grid.items() for coords in coords_list],
        columns=["Altitude", "Longitude", "Latitude"],
    )

    altitude_grid_geometry = [
        Point(xyz)
        for xyz in zip(
            altitude_grid_df["Latitude"],
            altitude_grid_df["Longitude"],
            altitude_grid_df["Altitude"],
        )
    ]
    gdf = gpd.GeoDataFrame(altitude_grid_df, geometry=altitude_grid_geometry, crs=crs)

    # Plot the points as a scatter plot in the 3D axis
    ax.scatter(
        gdf["Latitude"],
        gdf["Longitude"],
        gdf["Altitude"],
        c=gdf["Altitude"],  # Use altitude for color gradient
        cmap="viridis",  # Choose colormap for altitude
        marker="o",  # Set marker style
        alpha=0.2,
        depthshade=True,  # Enable depth shading for better visualization
    )

    ax.set_zlim(bottom=28_000)

    # Set labels for axes
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_zlabel("Altitude")

    return ax  # Return the modified axis


def display_flight_path_3d(flight_path, ax=None):
    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft"]
    )

    ax.plot(
        flight_path_df["longitude"],
        flight_path_df["latitude"],
        flight_path_df["altitude_ft"],
        color="k",
        markersize=10,
        linewidth=1,
    )


def show():
    plt.show()
