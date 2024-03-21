from config import Config, ContrailMaxConfig
import random
import warnings
from dotenv import load_dotenv
import pandas as pd

from routing_graph import RoutingGraphManager
from performance_model import PerformanceModel, RealFlight
from aco import ACO
from display import Display

if __name__ == "__main__":
    load_dotenv()
    warnings.filterwarnings("ignore")

    config = Config()

    # Construct all required grids + models
    routing_graph_manager = RoutingGraphManager(config)
    geodesic_path = routing_graph_manager.get_geodesic_path()
    routing_grid = routing_graph_manager.get_routing_grid()
    altitude_grid = routing_graph_manager.get_altitude_grid()

    performance_model = PerformanceModel(routing_graph_manager, config)
    cocip_manager = performance_model.get_cocip_manager()

    routing_graph_manager.set_performance_model(performance_model)

    # Run ACO
    ant_colony = ACO(routing_graph_manager, config)
    pareto_set = ant_colony.run_aco_colony()
    random_pareto_path = random.choice(pareto_set)

    # Run performance model on a real flight
    real_flight = RealFlight("jan-31.csv", routing_graph_manager, config)
    real_flight.run_performance_model()

    # Calculate CoCiP for both paths
    fp_ef, fp_df, fp_cocip = cocip_manager.calculate_ef_from_flight_path(
        real_flight.flight_path
    )
    aco_ef, aco_df, aco_cocip = cocip_manager.calculate_ef_from_flight_path(
        random_pareto_path.flight_path
    )

    # Create required dataframes
    grid = sum(routing_grid.get_routing_grid(), [])
    routing_grid_df = pd.DataFrame(grid, columns=["latitude", "longitude"])

    alt_grid_df = altitude_grid.copy()

    for alt in alt_grid_df:
        alt_grid_df[alt] = [x for x in sum(alt_grid_df[alt], []) if x is not None]

    alt_grid_df = pd.DataFrame(
        [
            (alt, *coords)
            for alt, coords_list in alt_grid_df.items()
            for coords in coords_list
        ],
        columns=["altitude", "longitude", "latitude"],
    )

    # Display results
    display = Display()
    blank = display.blank
    maps = display.maps
    _, objective_axs = blank.create_fig(3, 1)
    objectives = {
        key: [d[key] for d in ant_colony.objectives_over_time]
        for key in ant_colony.objectives_over_time[0]
    }
    for i, objective in enumerate(objectives):
        display.blank.show_plot(objective, objective_axs[i])

    _, map_axs = maps.create_fig(2, 1)
    maps.show_path(geodesic_path, map_axs[0])
    maps.show_path(real_flight.flight_path, map_axs[0])
    maps.set_title(map_axs[0], "BA177 Flight Path - Jan 31 2024")

    maps.show_path(geodesic_path, map_axs[1])
    maps.show_path(random_pareto_path.flight_path, map_axs[1])
    maps.set_title(map_axs[1], "ACO Flight Path")

    for ant_path in pareto_set:
        display.display_flight_path(ant_path.flight_path, map_axs[1])

    maps.show_grid(routing_grid_df, map_axs[0])

    maps.show_contrails(fp_cocip, map_axs[0])
    maps.show_contrails(aco_cocip, map_axs[1])

    display.show()
