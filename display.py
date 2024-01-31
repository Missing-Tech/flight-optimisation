from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from cartopy import crs as ccrs
from cartopy.feature import BORDERS, COASTLINE
from cartopy.mpl.patch import geos_to_path
import itertools
import numpy as np
import matplotlib.style as mplstyle
import time


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


def create_3d_ax(fig=None):
    if fig is None:
        fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    return fig, ax


def display_optimised_path(optimised_path, ax=None):
    if ax is None:
        _, ax = create_map_ax()

    routing_grid_df = pd.DataFrame(
        optimised_path, columns=["latitude", "longitude", "altitude"]
    )
    routing_grid_geometry = [
        Point(xy)
        for xy in zip(
            routing_grid_df["longitude"],
            routing_grid_df["latitude"],
        )
    ]
    gdf = gpd.GeoDataFrame(routing_grid_df, geometry=routing_grid_geometry, crs=wgs84)

    gdf_ae = gdf.to_crs(crs_proj4)

    ax.plot(
        routing_grid_df["longitude"],
        routing_grid_df["latitude"],
        color="k",
        markersize=10,
        linewidth=1,
        transform=ccrs.PlateCarree(),
    )


def display_flight_path(flight_path, ax=None):
    if ax is None:
        _, ax = create_map_ax()
    flight_path_df = pd.DataFrame(flight_path, columns=["latitude", "longitude"])

    ax.plot(
        flight_path_df["longitude"],
        flight_path_df["latitude"],
        color="k",
        markersize=10,
        linewidth=1,
        transform=ccrs.PlateCarree(),
    )


def display_contrails(contrails, ax=None):
    if ax is None:
        _, ax = create_map_ax()

    cocip.contrail.plot.scatter(
        "longitude", "latitude", c="rf_lw", ax=ax, transform=ccrs.PlateCarree()
    ),


def display_flight_headings(flight_path, ax=None):
    if ax is None:
        _, ax = create_map_ax()
    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "heading"]
    )
    headings = flight_path_df["heading"]
    heading_x = []
    heading_y = []
    for i in range(len(headings)):
        point = (flight_path_df["longitude"][i], flight_path_df["latitude"][i], 0)
        x, y, _ = util.calculate_new_coordinates(point, 200, headings[i])
        heading_x.append(x)
        heading_y.append(y)

    ax.quiver(
        downsampled_data.index.get_level_values("latitude"),
    )
    u, v = downsampled_data["eastward_wind"], downsampled_data["northward_wind"]

    # Overlay wind vectors using quiver plot
    ax.streamplot(
        lon,
        lat,
        u,
        v,
        color=(0.561, 0.898, 1, 0.42),
        transform=ccrs.PlateCarree(),
        density=1,
        linewidth=1,
    )


def display_geodesic_path(points, ax=None):
    if ax is None:
        _, ax = create_map_ax()
    geodesic_path_df = pd.DataFrame(
        points, columns=["Latitude", "Longitude", "Azimuth"]
    )
    geodesic_path_geometry = [
        Point(xy)
        for xy in zip(geodesic_path_df["Longitude"], geodesic_path_df["Latitude"])
    ]
    gdf = gpd.GeoDataFrame(geodesic_path_df, geometry=geodesic_path_geometry, crs=wgs84)
    gdf_ae = gdf.to_crs(crs_proj4)
    gdf_ae.plot(ax=ax, color="red", markersize=5)


def display_routing_grid(grid, ax=None):
    if ax is None:
        _, ax = create_map_ax()

    grid = sum(grid, [])

    routing_grid_df = pd.DataFrame(grid, columns=["Latitude", "Longitude"])
    routing_grid_geometry = [
        Point(xy)
        for xy in zip(
            routing_grid_df["Longitude"],
            routing_grid_df["Latitude"],
        )
    ]
    gdf = gpd.GeoDataFrame(routing_grid_df, geometry=routing_grid_geometry, crs=wgs84)

    gdf_ae = gdf.to_crs(crs_proj4)

    gdf_ae.plot(ax=ax, color="blue", markersize=1)


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
    if ax is None:
        fig, ax = create_3d_ax()

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

    flight_path_df = pd.DataFrame(
        flight_path, columns=["latitude", "longitude", "altitude_ft"]
    )
    flight_path_geometry = [
        Point(xyz)
        for xyz in zip(
            flight_path_df["latitude"],
            flight_path_df["longitude"],
            flight_path_df["altitude_ft"],
        )
    ]
    gdf = gpd.GeoDataFrame(flight_path_df, geometry=flight_path_geometry, crs=crs)

    ax.plot(
        gdf["longitude"],
        gdf["latitude"],
        gdf["altitude_ft"],
        color="k",
        markersize=10,
        linewidth=5,
    )

    ax.set_zlim(bottom=28_000)

    # Set labels for axes
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_zlabel("Altitude")

    return ax  # Return the modified axis


def display_flight_path_3d(flight_path, ax=None):
    if ax is None:
        fig, ax = create_3d_ax()
    flight_path_df = pd.DataFrame(
        flight_path, columns=["Latitude", "Longitude", "Altitude"]
    )
    flight_path_geometry = [
        Point(xyz)
        for xyz in zip(
            flight_path_df["Latitude"],
            flight_path_df["Longitude"],
            flight_path_df["Altitude"],
        )
    ]
    gdf = gpd.GeoDataFrame(flight_path_df, geometry=flight_path_geometry, crs=crs)

    ax.plot(
        gdf["Longitude"],
        gdf["Latitude"],
        gdf["Altitude"],
        color="k",
        markersize=10,
        linewidth=1,
    )


def display_issrs(ax=None):
    if ax is None:
        ax = create_map_ax()

    issr_geometry = [
        Point(xy)
        for xy in zip(
            issrs.da["latitude"],
            issrs.da["longitude"],
        )
    ]

    gdf = gpd.GeoDataFrame(issrs.da, geometry=issr_geometry, crs=crs)

    gdf.plot(
        ax=ax,
        column="issr",
        cmap="Reds",
        alpha=0.5,
        transform=ccrs.PlateCarree(),
    )


def show():
    plt.show()
