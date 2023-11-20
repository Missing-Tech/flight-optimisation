from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import warnings
import geodesic_path as gp
from cartopy import crs as ccrs
from cartopy.feature import BORDERS, COASTLINE
import routing_grid as rg
from cartopy.mpl.patch import geos_to_path
import itertools
import numpy as np

warnings.filterwarnings("ignore")

lon0, lat0 = 0.5, 51.4
lon1, lat1 = -73.7, 40.6
no_of_points = 20

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
    return ax


def create_3d_ax(fig=None):
    if fig is None:
        fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    return ax


points = gp.calculate_path(no_of_points, (lat0, lon0, 0), (lat1, lon1, 0))
grid = rg.calculate_routing_grid(5, points)


def display_wind_vectors(downsample_factor=755, ax=None):
    if ax is None:
        ax = create_map_ax()
    wind_data = pd.read_csv("output_data.csv", sep=",")
    downsampled_data = wind_data.loc[::downsample_factor, :]
    lon, lat = downsampled_data["longitude"], downsampled_data["latitude"]
    u, v = downsampled_data["u"], downsampled_data["v"]

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


def display_geodesic_path(points=points, ax=None):
    if ax is None:
        ax = create_map_ax()
    geodesic_path_df = pd.DataFrame(
        points, columns=["Latitude", "Longitude", "Azimuth"]
    )
    geodesic_path_geometry = [
        Point(xy)
        for xy in zip(geodesic_path_df["Longitude"], geodesic_path_df["Latitude"])
    ]
    gdf = gpd.GeoDataFrame(geodesic_path_df, geometry=geodesic_path_geometry, crs=wgs84)
    gdf_ae = gdf.to_crs(crs_proj4)
    gdf_ae.plot(ax=ax, color="red", markersize=10)


def display_routing_grid(grid=grid, ax=None):
    if ax is None:
        ax = create_map_ax()

    grid = sum(grid, [])

    routing_grid_df = pd.DataFrame(grid, columns=["Latitude", "Longitude", "Altitude"])
    altitude_30000 = routing_grid_df[routing_grid_df["Altitude"] == 30_000]
    routing_grid_geometry = [
        Point(xy)
        for xy in zip(
            altitude_30000["Longitude"],
            altitude_30000["Latitude"],
        )
    ]
    gdf = gpd.GeoDataFrame(altitude_30000, geometry=routing_grid_geometry, crs=wgs84)

    gdf_ae = gdf.to_crs(crs_proj4)

    gdf_ae.plot(ax=ax, color="blue", markersize=2)


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
def display_altitude_grid_3d(grid=grid, ax=None):
    if ax is None:
        ax = create_3d_ax()

    lc = extract_map_geometry()
    ax.add_collection3d(lc, zs=28_000, zdir="z")

    grid = sum(grid, [])
    altitude_grid_df = pd.DataFrame(grid, columns=["Longitude", "Latitude", "Altitude"])
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
        depthshade=True,  # Enable depth shading for better visualization
    )

    ax.set_zlim(bottom=28_000)

    # Set labels for axes
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_zlabel("Altitude")

    return ax  # Return the modified axis


# Create a subplots for 3D scatter plot and the map
ax1 = create_map_ax()
ax2 = create_3d_ax()

display_geodesic_path(ax=ax1)
display_routing_grid(ax=ax1)
display_wind_vectors(ax=ax1)
display_altitude_grid_3d(ax=ax2)

plt.show()
