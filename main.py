import display
from config import Config
import random
import warnings
from dotenv import load_dotenv

from routing_graph import RoutingGraphManager
from performance_model import PerformanceModel
from aco import ACO, RealFlight

if __name__ == "__main__":
    load_dotenv()
    warnings.filterwarnings("ignore")

    config = Config()

    routing_graph_manager = RoutingGraphManager(config)
    geodesic_path = routing_graph_manager.get_geodesic_path()
    routing_grid = routing_graph_manager.get_routing_grid()
    altitude_grid = routing_graph_manager.get_altitude_grid()

    performance_model = PerformanceModel(altitude_grid, config)
    contrail_grid = performance_model.get_contrail_grid()
    cocip_manager = performance_model.get_cocip_manager()
    weather_grid = performance_model.get_weather_grid()
    apm = performance_model.get_apm()

    routing_graph = routing_graph_manager.get_routing_graph(contrail_grid)

    ant_colony = ACO(routing_graph, altitude_grid, contrail_grid, apm, config)

    real_flight = RealFlight("jan-31.csv", altitude_grid, routing_graph, apm, config)
    real_flight.run_performance_model()

    _, ax_blank = display.create_blank_ax()
    # fig_map, ax_map = display.create_map_ax()
    fig_side, ax_side_1, ax_side_2 = display.create_side_by_side_ax()
    # fig_side, ax_side_3, ax_side_4 = display.create_side_by_side_ax()
    # fig_3d, ax_3d = display.create_3d_ax()
    #

    pareto_set = ant_colony.run_aco_colony()
    random_pareto_path = random.choice(pareto_set)

    fp_ef, fp_df, fp_cocip = cocip_manager.calculate_ef_from_flight_path(
        real_flight.flight_path
    )
    aco_ef, aco_df, aco_cocip = cocip_manager.calculate_ef_from_flight_path(
        random_pareto_path.flight_path
    )

    display.display_objective_over_iterations(ant_colony.objectives_over_time, ax_blank)

    # display.display_routing_grid(routing_grid.get_routing_grid(), ax_map)

    # aco_ani = display.create_aco_animation(
    #     ant_paths, best_indexes, ax=ax_map, fig=fig_map
    # )

    for ant_path in pareto_set:
        display.display_flight_path(ant_path, ax_side_1)

    # display.display_flight_altitude(best_path, ax_blank)
    # display.display_flight_altitude(real_flight_path, ax_blank, "r")

    # display.display_flight_path(real_flight_path, ax_map)
    # display.display_geodesic_path(geodesic_path, ax=ax_map)
    display.display_geodesic_path(geodesic_path, ax=ax_side_1)
    display.display_geodesic_path(geodesic_path, ax=ax_side_2)
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
    display.display_flight_path(
        random_pareto_path.flight_path, ax_side_1, linewidth=1, color="r"
    )
    display.display_flight_path(real_flight.flight_path, ax_side_2)
    display.display_flight_ef(aco_cocip, ax_side_1)
    display.display_flight_ef(fp_cocip, ax_side_2)
    ax_side_1.set_title("ACO Flight Path")
    ax_side_2.set_title("BA177 Flight Path")

    display.show()
