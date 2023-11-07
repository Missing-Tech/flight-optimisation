import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from geodatasets import get_path
from pyproj import Geod
from shapely.geometry import Point
import geodesic_path as gp
import routing_grid as rg
import util

lon0, lat0 =  0, 50
lon1, lat1 =  -72, 46
no_of_points = 20

points = gp.calculate_path(util.R, no_of_points, (lat0, lon0, 90), (lat1, lon1, 90))
grid = rg.RoutingGrid().calculate_routing_grid(5, (lat0, lon0, 90), (lat1, lon1, 90), util.R, no_of_points)

path = get_path("naturalearth.land")
geoid = Geod(ellps="sphere", a=util.R, b=util.R)
geodesic_path_df = pd.DataFrame(points, columns=['Latitude', 'Longitude', 'Azimuth'])
routing_grid_df = pd.DataFrame(grid, columns=['Latitude', 'Longitude', 'Azimuth'])
geodesic_path_geometry = [Point(xy) for xy in zip(geodesic_path_df['Longitude'], geodesic_path_df['Latitude'])]
routing_grid_geometry = [Point(xy) for xy in zip(routing_grid_df['Longitude'], routing_grid_df['Latitude'])]
gdf = gpd.GeoDataFrame(geodesic_path_df, geometry=geodesic_path_geometry) 
gdf2 = gpd.GeoDataFrame(routing_grid_df, geometry=routing_grid_geometry) 

ax = gpd.read_file(path).plot()
gdf.plot(ax=ax, color='red', markersize=10)
gdf2.plot(ax=ax, color='blue', markersize=2)
plt.show()