import display
import flight_path as fp
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
import pandas as pd
from pycontrails.models.ps_model import PSGrid

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
contrail_grid = ct.download_contrail_grid(altitude_grid, "contrail_grid.nc", "netcdf")
contrail_polys = ct.download_contrail_grid(
    altitude_grid, "contrail_polys.json", "geojson"
)
routing_graph = rgraph.calculate_routing_graph(altitude_grid, distance_between_points)


flight_path_df = pd.read_csv("jan-31.csv")
flight_path_df = flight_path_df[flight_path_df["AltMSL"] > 30000]

# _, ax_blank = display.create_blank_ax()
# fig_map, ax_map = display.create_map_ax()
fig_side, ax_side_1, ax_side_2 = display.create_side_by_side_ax()
# fig_3d, ax_3d = display.create_3d_ax()

ant_paths, aco_path = aco.run_aco_colony(
    config.NO_OF_ITERATIONS,
    config.NO_OF_ANTS,
    routing_graph,
    altitude_grid,
    distance_between_points,
)

real_flight_path = util.convert_real_flight_path(flight_path_df)
real_flight_path = fp.calculate_flight_characteristics(real_flight_path, weather_data)
real_flight_path = fp.calculate_flight_fuel_flow(real_flight_path)
aco_path = fp.calculate_flight_fuel_flow(aco_path)

fp_ef, fp_df, fp_cocip = ct.calculate_ef_from_flight_path(real_flight_path)
aco_ef, aco_df, aco_cocip = ct.calculate_ef_from_flight_path(aco_path)


# display.display_optimised_path(best_path, ax1)
# display.display_flight_altitude(best_path, ax_blank)
# display.display_flight_altitude(real_flight_path, ax_blank, "r")

# display.display_flight_path(real_flight_path, ax_map)
# display.display_geodesic_path(points, ax=ax1)
# display.display_flight_path_3d(real_flight_path, ax=ax_3d)
# ani = display.create_flight_animation(
#     best_path, contrail_grid, fig=fig_side, ax=ax_side_1, title="ACO Flight Path"
# )
# ani2 = display.create_flight_animation(
#     real_flight_path,
#     contrail_grid,
#     fig=fig_side,
#     ax=ax_side_2,
#     title="BA177 Flight Path",
# )
display.display_flight_path(aco_path, ax_side_1)
display.display_flight_path(real_flight_path, ax_side_2)
display.display_flight_ef(aco_cocip, ax_side_1)
display.display_flight_ef(fp_cocip, ax_side_2)
ax_side_1.set_title("ACO Flight Path")
ax_side_2.set_title("BA177 Flight Path")

# 3d_ani = display.create_3d_flight_animation(
#     best_path, contrail_grid, contrail_polys, fig=fig_3d, ax=ax_3d
# )


display.show()
