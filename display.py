import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import warnings
import geodesic_path as gp
from cartopy import crs as ccrs
from cartopy.feature import OCEAN, LAND, BORDERS
import routing_grid as rg

warnings.filterwarnings("ignore")

lon0, lat0 = -3.7, 40.4
lon1, lat1 =  24.9, 60.1
no_of_points = 20

crs = ccrs.LambertConformal(central_longitude=10, central_latitude=50)
crs_proj4 = crs.proj4_init

epsg = "EPSG:4326"

ax = plt.axes(projection=crs)
ax.set_extent([-20, 40, 35, 70])
ax.add_feature(BORDERS, lw=0.5, color="gray")
ax.gridlines(draw_labels=True, color="gray", alpha=0.5, ls="--")
ax.coastlines(resolution="50m", lw=0.5, color="gray")

points = gp.calculate_path(no_of_points, (lat0, lon0, 0), (lat1, lon1, 0))
geodesic_path_df = pd.DataFrame(points, columns=['Latitude', 'Longitude', 'Azimuth'])
geodesic_path_geometry = [Point(xy) for xy in zip(geodesic_path_df['Longitude'], geodesic_path_df['Latitude'])]
gdf = gpd.GeoDataFrame(geodesic_path_df, geometry=geodesic_path_geometry, crs=epsg) 

grid = rg.RoutingGrid().calculate_routing_grid(5, points, no_of_points)
routing_grid_df = pd.DataFrame(grid, columns=['Latitude', 'Longitude', 'Azimuth'])
routing_grid_geometry = [Point(xy) for xy in zip(routing_grid_df['Longitude'], routing_grid_df['Latitude'])]
gdf2 = gpd.GeoDataFrame(routing_grid_df, geometry=routing_grid_geometry, crs=epsg) 

gdf_ae = gdf.to_crs(crs_proj4)
gdf2_ae = gdf2.to_crs(crs_proj4)

gdf_ae.plot(ax=ax, color='red', markersize=10)
gdf2_ae.plot(ax=ax, color='blue', markersize=2)

plt.show()