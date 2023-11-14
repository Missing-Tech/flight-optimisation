import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import warnings
import geodesic_path as gp
from cartopy import crs as ccrs
from cartopy.feature import BORDERS 
import routing_grid as rg

warnings.filterwarnings("ignore")

lon0, lat0 = 0.5, 51.4
lon1, lat1 =  -73.7 ,40.6
no_of_points = 20

crs = ccrs.NearsidePerspective(central_latitude=51, central_longitude=-35)
crs_proj4 = crs.proj4_init

wgs84 = "WGS84"

ax = plt.axes(projection=crs)
ax.set_extent([10, -90, 25, 60])
ax.add_feature(BORDERS, lw=0.5, color="gray")
ax.gridlines(draw_labels=True, color="gray", alpha=0.5, ls="--")
ax.coastlines(resolution="50m", lw=0.5, color="gray")

points = gp.calculate_path(no_of_points, (lat0, lon0, 0), (lat1, lon1, 0))
geodesic_path_df = pd.DataFrame(points, columns=['Latitude', 'Longitude', 'Azimuth'])
geodesic_path_geometry = [Point(xy) for xy in zip(geodesic_path_df['Longitude'], geodesic_path_df['Latitude'])]
gdf = gpd.GeoDataFrame(geodesic_path_df, geometry=geodesic_path_geometry, crs=wgs84) 

grid = rg.RoutingGrid().calculate_routing_grid(5, points)
routing_grid_df = pd.DataFrame(grid, columns=['Latitude', 'Longitude', 'Azimuth'])
routing_grid_geometry = [Point(xy) for xy in zip(routing_grid_df['Longitude'], routing_grid_df['Latitude'])]
gdf2 = gpd.GeoDataFrame(routing_grid_df, geometry=routing_grid_geometry, crs=wgs84) 

gdf_ae = gdf.to_crs(crs_proj4)
gdf2_ae = gdf2.to_crs(crs_proj4)



downsample_factor = 25
wind_data = pd.read_csv("output_data.csv", sep=",")
downsampled_data = wind_data.loc[::downsample_factor, :]

gdf_ae.plot(ax=ax, color='red', markersize=10)
gdf2_ae.plot(ax=ax, color='blue', markersize=2)

# Quiver plot for downsampled wind vectors
ax.quiver(
    downsampled_data['longitude'],
    downsampled_data['latitude'],
    downsampled_data['u'],
    downsampled_data['v'],
    transform=ccrs.PlateCarree(),
    color=(0.73, 0.93, 1, 0.8),
    scale_units='xy',
    angles='xy',
    width=0.005,
)


plt.show()