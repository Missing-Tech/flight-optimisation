import display
import geodesic_path as gp
import flight_path as fp
import config
import contrails as ct
import warnings
import altitude_grid as ag
import pandas as pd
import ecmwf
import util
import routing_grid as rg
import aco
import routing_graph as rgraph
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    warnings.filterwarnings("ignore")

    altitude_grid = ag.get_altitude_grid()

    metGrid = ecmwf.MetAltitudeGrid(altitude_grid)
    contrail_grid = ct.get_contrail_grid()
    contrail_polys = ct.get_contrail_polys()
    routing_graph = rgraph.get_routing_graph()

    ant_colony = aco.ACO(routing_graph, altitude_grid, contrail_grid)

    flight_path_df = pd.read_csv("data/jan-31.csv")
    flight_path_df = flight_path_df[flight_path_df["AltMSL"] > 30000]

    _, ax_blank = display.create_blank_ax()
    fig_map, ax_map = display.create_map_ax()
    fig_side, ax_side_1, ax_side_2 = display.create_side_by_side_ax()
    # fig_side, ax_side_3, ax_side_4 = display.create_side_by_side_ax()
    # fig_3d, ax_3d = display.create_3d_ax()
    #

    ant_paths, aco_path, objectives_dataframe, best_indexes = ant_colony.run_aco_colony(
        config.NO_OF_ITERATIONS,
        config.NO_OF_ANTS,
    )

    objectives_dataframe.to_csv("data/objectives.csv")

    real_flight_path = util.convert_real_flight_path(flight_path_df, metGrid)
    real_flight_path = fp.calculate_flight_characteristics(real_flight_path)

    fp_ef, fp_df, fp_cocip = ct.calculate_ef_from_flight_path(real_flight_path)
    aco_ef, aco_df, aco_cocip = ct.calculate_ef_from_flight_path(aco_path)

    aco_objective = ant_colony.calculate_objective_dataframe(aco_path)
    fp_objective = ant_colony.calculate_objective_dataframe(real_flight_path)
    print(f"ACO Objective: {aco_objective.to_dict()}")
    print(f"FP Objective: {fp_objective.to_dict()}")

    display.display_objective_over_iterations(objectives_dataframe, ax_blank)

    aco_ani = display.create_aco_animation(
        ant_paths, best_indexes, ax=ax_map, fig=fig_map
    )

    # for ant_path in ant_paths:
    #     display.display_flight_path(ant_path, ax_side_1)
    #
    # display.display_flight_altitude(best_path, ax_blank)
    # display.display_flight_altitude(real_flight_path, ax_blank, "r")

    display.display_routing_grid(rg.get_routing_grid(), ax=ax_side_1)
    # display.display_flight_path(real_flight_path, ax_map)
    display.display_geodesic_path(gp.get_geodesic_path(), ax=ax_side_2)
    display.display_geodesic_path(gp.get_geodesic_path(), ax=ax_side_1)
    # display.display_flight_path_3d(real_flight_path, ax=ax_3d)
    # ani_3d = display.create_3d_flight_animation(
    #     aco_path, contrail_grid, contrail_polys, fig=fig_3d, ax=ax_3d
    # )
    #

    # display.display_wind_vectors(metGrid.weather_data, ax=ax_side_1)
    # display.display_wind_vectors(metGrid.weather_data, ax=ax_side_2)

    # ani = display.create_flight_animation(
    #     aco_path, contrail_grid, fig=fig_side, ax=ax_side_3, title="ACO Flight Path"
    # )
    # ani2 = display.create_flight_animation(
    #     real_flight_path,
    #     contrail_grid,
    #     fig=fig_side,
    #     ax=ax_side_4,
    #     title="BA177 Flight Path",
    # )
    display.display_flight_path(aco_path, ax_side_1)
    display.display_flight_path(real_flight_path, ax_side_2)
    display.display_flight_ef(aco_cocip, ax_side_1)
    display.display_flight_ef(fp_cocip, ax_side_2)
    ax_side_1.set_title("ACO Flight Path")
    ax_side_2.set_title("BA177 Flight Path")

    display.show()
