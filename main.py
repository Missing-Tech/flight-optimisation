import display
import warnings
import geodesic_path as gp
import routing_grid as rg
import altitude_grid as ag
import ecmwf
import util
import aco
import routing_graph as rgraph

warnings.filterwarnings("ignore")

lon0, lat0 = 0.5, 51.4
lon1, lat1 = -73.7, 40.6
no_of_points = 25

points = gp.calculate_path(no_of_points, (lat0, lon0, 0), (lat1, lon1, 0))
grid = rg.calculate_routing_grid(5, points)
altitude_grid = ag.calculate_altitude_grid(grid)
weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
routing_graph = rgraph.calculate_routing_graph(altitude_grid)

fig1, ax1 = display.create_map_ax()


ant_paths = aco.run_aco_colony(50, 50, routing_graph)
for path in ant_paths:
    optimised_path = util.convert_indices_to_points(path, altitude_grid)
    display.display_optimised_path(optimised_path, ax1)

display.display_routing_grid(grid, ax1)

display.show()
