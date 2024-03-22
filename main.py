from config import Config, ContrailMaxConfig
import random
import warnings
from dotenv import load_dotenv
import pandas as pd
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from routing_graph import RoutingGraphManager
from performance_model import PerformanceModel, RealFlight
from aco import ACO
from display import Display


def main():
    config = Config()

    # Construct all required grids + models
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating altitude grid...", total=None)
        routing_graph_manager = RoutingGraphManager(config)
        geodesic_path = routing_graph_manager.get_geodesic_path()
        routing_grid = routing_graph_manager.get_routing_grid()
        altitude_grid = routing_graph_manager.get_altitude_grid()
    print("[bold green]:white_check_mark: Altitude grid constructed.[/bold green]")

    # Construct performance model
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating performance model...", total=None)
        performance_model = PerformanceModel(routing_graph_manager, config)
        cocip_manager = performance_model.get_cocip_manager()
        routing_graph_manager.set_performance_model(performance_model)
    print("[bold green]:white_check_mark: Performance model constructed.[/bold green]")

    _ = routing_graph_manager.get_routing_graph()

    # Run ACO
    ant_colony = ACO(routing_graph_manager, config)
    pareto_set = ant_colony.run_aco_colony()
    print("[bold green]:white_check_mark: ACO complete.[/bold green]")
    random_pareto_path = random.choice(pareto_set)

    # Run performance model on a real flight
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Running performance model on real flight...", total=None
        )
        real_flight = RealFlight("jan-31.csv", routing_graph_manager, config)
        real_flight.run_performance_model()
    print(
        "[bold green]:white_check_mark: Performance model run on real flight.[/bold green]"
    )

    # Calculate CoCiP for both paths
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Running CoCiP for both flights...", total=None)
        fp_ef, fp_df, fp_cocip = cocip_manager.calculate_ef_from_flight_path(
            real_flight.flight_path
        )
        aco_ef, aco_df, aco_cocip = cocip_manager.calculate_ef_from_flight_path(
            random_pareto_path.flight_path
        )
    print(
        "[bold green]:white_check_mark: CoCiP calculated for both flights.[/bold green]"
    )

    # Create required dataframes
    grid = sum(routing_grid.get_routing_grid(), [])
    routing_grid_df = pd.DataFrame(grid, columns=["latitude", "longitude"])

    # alt_grid_df = altitude_grid
    #
    # for alt in alt_grid_df:
    #     alt_grid_df[alt] = [x for x in sum(alt_grid_df[alt], []) if x is not None]
    #
    # alt_grid_df = pd.DataFrame(
    #     [
    #         (alt, *coords)
    #         for alt, coords_list in alt_grid_df.items()
    #         for coords in coords_list
    #     ],
    #     columns=["altitude", "longitude", "latitude"],
    # )

    geodesic_path = pd.DataFrame(
        geodesic_path, columns=["latitude", "longitude", "azimuth"]
    )
    real_flight_df = pd.DataFrame(
        real_flight.flight_path, columns=["latitude", "longitude"]
    )
    random_pareto_path_df = pd.DataFrame(
        random_pareto_path.flight_path, columns=["latitude", "longitude"]
    )

    objectives = {key: [] for key in ant_colony.objectives_over_time[0].keys()}
    for entry in ant_colony.objectives_over_time:
        for key, value in entry.items():
            objectives[key].append(value)

    # Display results
    display = Display()
    blank = display.blank
    maps = display.maps
    _, objective_axs = blank.create_fig(3, 1)

    # Show objectives over time
    display.blank.show_plot(
        objectives["contrail"],
        objective_axs[0],
        color="b",
        title="Lowest contrail EF over iterations",
        x_label="Iteration",
        y_label="EF",
    )
    display.blank.show_plot(
        objectives["co2"],
        objective_axs[1],
        color="r",
        title="Least kg of CO2 over iterations",
        x_label="Iteration",
        y_label="kg of CO2",
    )
    display.blank.show_plot(
        objectives["time"],
        objective_axs[2],
        color="g",
        title="Shortest time over iterations",
        x_label="Iteration",
        y_label="Time (s)",
    )

    _, map_axs = maps.create_fig(2, 1)
    maps.show_path(geodesic_path, map_axs[0], linestyle="--")
    maps.show_path(real_flight_df, map_axs[0], color="red", linewidth=1)
    maps.set_title(map_axs[0], "BA177 Flight Path - Jan 31 2024")

    maps.show_path(geodesic_path, map_axs[1], linestyle="--")
    maps.show_path(random_pareto_path_df, map_axs[1], color="red", linewidth=1)
    maps.set_title(map_axs[1], "ACO Flight Path")

    for ant_path in pareto_set:
        path_df = pd.DataFrame(ant_path.flight_path, columns=["latitude", "longitude"])
        maps.show_path(path_df, map_axs[1], color="gray", linewidth=0.5)

    maps.show_grid(routing_grid_df, map_axs[1])

    maps.show_contrails(fp_cocip, map_axs[0])
    maps.show_contrails(aco_cocip, map_axs[1])

    display.show()


if __name__ == "__main__":
    app = typer.Typer()
    load_dotenv()
    warnings.filterwarnings("ignore")
    typer.run(main)
