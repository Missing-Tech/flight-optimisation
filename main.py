import display
import flight_path as fp
import config
import contrails as ct
import warnings
import altitude_grid as ag
import pandas as pd
import ecmwf
import util
import aco
import routing_graph as rgraph
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore")

altitude_grid = ag.get_altitude_grid()

weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
contrail_grid = ct.get_contrail_grid()
contrail_polys = ct.get_contrail_polys()
routing_graph = rgraph.get_routing_graph()

flight_path_df = pd.read_csv("jan-31.csv")
flight_path_df = flight_path_df[flight_path_df["AltMSL"] > 30000]

# _, ax_blank = display.create_blank_ax()
# fig_map, ax_map = display.create_map_ax()
fig_side, ax_side_1, ax_side_2 = display.create_side_by_side_ax()
fig_side, ax_side_3, ax_side_4 = display.create_side_by_side_ax()
fig_3d, ax_3d = display.create_3d_ax()

ant_paths, aco_path = aco.run_aco_colony(
    config.NO_OF_ITERATIONS,
    config.NO_OF_ANTS,
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
# ani_3d = display.create_3d_flight_animation(
#     aco_path, contrail_grid, contrail_polys, fig=fig_3d, ax=ax_3d
# )
ani = display.create_flight_animation(
    aco_path, contrail_grid, fig=fig_side, ax=ax_side_3, title="ACO Flight Path"
)
ani2 = display.create_flight_animation(
    real_flight_path,
    contrail_grid,
    fig=fig_side,
    ax=ax_side_4,
    title="BA177 Flight Path",
)
display.display_flight_path(aco_path, ax_side_1)
display.display_flight_path(real_flight_path, ax_side_2)
display.display_flight_ef(aco_cocip, ax_side_1)
display.display_flight_ef(fp_cocip, ax_side_2)
ax_side_1.set_title("ACO Flight Path")
ax_side_2.set_title("BA177 Flight Path")


display.show()
