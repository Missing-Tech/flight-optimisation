import display
import config
import contrails as ct
import warnings
import geodesic_path as gp
import routing_grid as rg
import altitude_grid as ag
import ecmwf
import util
import aco
import routing_graph as rgraph
from cartopy import crs as ccrs
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore")

lat0, lon0 = config.DEPARTURE_AIRPORT
lat1, lon1 = config.DESTINATION_AIRPORT
distance_between_points = gp.calculate_distance_between_points(
    config.NO_OF_POINTS, (lat0, lon0, 0), (lat1, lon1, 0)
)

points = gp.calculate_path(config.NO_OF_POINTS, (lat0, lon0, 0), (lat1, lon1, 0))
grid = rg.calculate_routing_grid(points)
altitude_grid = ag.calculate_altitude_grid(grid)
weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
contrail_grid = ct.download_contrail_grid(altitude_grid)
routing_graph = rgraph.calculate_routing_graph(altitude_grid, distance_between_points)


fig1, ax1 = display.create_map_ax()
da = contrail_grid["ef_per_m"]
display.display_contrail_grid(da, ax1)

ant_paths, best_path = aco.run_aco_colony(
    config.NO_OF_ITERATIONS,
    config.NO_OF_ANTS,
    routing_graph,
    altitude_grid,
    distance_between_points,
)
# for path in ant_paths:
#     display.display_optimised_path(path, ax1, linewidth=0.5)

display.display_optimised_path(best_path, ax1)

display.display_routing_grid(grid, ax1)


display.show()
