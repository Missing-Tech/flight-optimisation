from __future__ import print_function, unicode_literals
import random
import warnings
from dotenv import load_dotenv
import pandas as pd
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
import inquirer
from matplotlib.patches import Patch
import numpy as np

from matplotlib.collections import PolyCollection
import shapely
import json

from config import Config, ContrailMaxConfig
from routing_graph import RoutingGraphManager
from performance_model import PerformanceModel, RealFlight
from aco import ACO
from display import Display


def show_objectives_over_time(display, objectives):
    blank = display.blank
    _, objective_axs = blank.create_fig(3, 1)

    # Show objectives over time
    blank.show_plot(
        objectives["contrail"],
        objective_axs[0],
        color="b",
        title="Lowest contrail EF over iterations",
        x_label="Iteration",
        y_label="EF",
    )
    blank.show_plot(
        objectives["co2"],
        objective_axs[1],
        color="r",
        title="Least kg of CO2 over iterations",
        x_label="Iteration",
        y_label="kg of CO2",
    )
    blank.show_plot(
        objectives["time"],
        objective_axs[2],
        color="g",
        title="Shortest time over iterations",
        x_label="Iteration",
        y_label="Time (s)",
    )


def show_flight_frames(display, real_flight_df, aco_path, contrail_grid, config):
    maps = display.maps
    fig, map_axs = maps.create_fig(2, 2)

    fig.title = "Flight Path Comparison"

    time = aco_path["time"].min()
    aco_cutoff_df = get_path_before_time(aco_path, time)

    legend_patches = [
        Patch(color="blue", label="BA177 Flight Path"),
        Patch(color="red", label="ACO Flight Path"),
    ]

    timestamps = contrail_grid["time"]
    fig.legend(handles=legend_patches)

    for ax in map_axs:
        flight_duration = real_flight_df["time"].max() - real_flight_df["time"].min()
        time_step = flight_duration / len(map_axs)
        time = time + pd.Timedelta(time_step)

        aco_cutoff_df = get_path_before_time(aco_path, time)
        real_cutoff_df = get_path_before_time(real_flight_df, time)
        maps.show_path(real_cutoff_df, ax, color="blue", linewidth=2)
        maps.show_path(aco_cutoff_df, ax, color="red", linewidth=2)
        ax.set_title("Time: {}".format(time))
        #
        # Interpolate contrail grid data at the given timestamp
        nearest_timestamp_index = np.argmin(
            np.abs(timestamps - np.datetime64(time)).values
        )
        nearest_flight_level_index = np.argmin(
            np.abs(config.FLIGHT_LEVELS - (aco_cutoff_df["altitude_ft"].iloc[-1] / 100))
        )
        interpolated_grid = contrail_grid.isel(
            flight_level=nearest_flight_level_index, time=nearest_timestamp_index
        )
        maps.show_contrail_grid(interpolated_grid, ax)


def get_path_before_time(path, time):
    time = pd.Timestamp(time)
    return path[path["time"] <= time]


def show_3d_flight_frames(
    display, real_flight_df, aco_path, contrail_polys, contrail_grid, config
):
    def get_contrail_polys_at_time(contrail_polys, time):
        collections = {}
        polys = contrail_polys["polys"]
        for level in config.FLIGHT_LEVELS:
            patches = []
            for poly in polys:
                if (
                    poly["properties"]["level"] == level
                    and poly["properties"]["time"] == time
                ):
                    multipoly = shapely.from_geojson(json.dumps(poly))
                    for geom in multipoly.geoms:
                        geom = geom.simplify(0.3)
                        x, y = geom.exterior.coords.xy
                        patches.append(np.asarray(tuple(zip(x, y))))
            collection = PolyCollection(patches, facecolor="red", alpha=0.3)
            collections[level] = collection

        return collections

    def convert_time_string(time):
        new_time_str = np.datetime_as_string(time, unit="s") + "Z"
        return new_time_str

    maps = display.maps3d
    fig, map_axs = maps.create_fig(2, 2)

    fig.title = "Flight Path Comparison"

    time = aco_path["time"].min()
    aco_cutoff_df = get_path_before_time(aco_path, time)

    legend_patches = [
        Patch(color="blue", label="BA177 Flight Path"),
        Patch(color="red", label="ACO Flight Path"),
    ]

    fig.legend(handles=legend_patches)

    for ax in map_axs:
        flight_duration = real_flight_df["time"].max() - real_flight_df["time"].min()
        time_step = flight_duration / len(map_axs)
        time = time + pd.Timedelta(time_step)

        aco_cutoff_df = get_path_before_time(aco_path, time)
        real_cutoff_df = get_path_before_time(real_flight_df, time)
        maps.show_3d_path(real_cutoff_df, ax, color="blue", linewidth=2)
        maps.show_3d_path(aco_cutoff_df, ax, color="red", linewidth=2)
        ax.set_title("Time: {}".format(time))

        timestamps = contrail_grid["time"]

        # Interpolate contrail grid data at the given timestamp
        nearest_timestamp_index = np.argmin(
            np.abs(timestamps - np.datetime64(time)).values
        )
        time_string = convert_time_string(
            contrail_grid["time"][nearest_timestamp_index].values
        )
        # Interpolate contrail grid data at the given timestamp
        polys_at_time = get_contrail_polys_at_time(contrail_polys, time_string)
        for level in polys_at_time:
            ax.add_collection3d(polys_at_time[level], zs=level * 100, zdir="z")


def show_flight_path_comparison(
    display,
    geodesic_path,
    real_flight_df,
    random_pareto_path_df,
    pareto_set,
    fp_cocip,
    aco_cocip,
):
    maps = display.maps
    _, map_axs = maps.create_fig(2, 1)
    maps.show_path(geodesic_path, map_axs[0], linestyle="--")
    maps.show_path(real_flight_df, map_axs[0], color="red", linewidth=2)
    maps.set_title(map_axs[0], "BA177 Flight Path - Jan 31 2024")

    maps.show_path(geodesic_path, map_axs[1], linestyle="--")
    maps.show_path(random_pareto_path_df, map_axs[1], color="red", linewidth=2)
    maps.set_title(map_axs[1], "ACO Flight Path")

    for ant_path in pareto_set:
        path_df = pd.DataFrame(ant_path.flight_path, columns=["latitude", "longitude"])
        maps.show_path(path_df, map_axs[1], color="gray", linewidth=0.5)

    maps.show_contrails(fp_cocip, map_axs[0])
    maps.show_contrails(aco_cocip, map_axs[1])


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
        contrail_grid = performance_model.get_contrail_grid()
        contrail_polys = performance_model.get_contrail_polys()
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
        real_flight.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )
    random_pareto_path_df = pd.DataFrame(
        random_pareto_path.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )

    objectives = {key: [] for key in ant_colony.objectives_over_time[0].keys()}
    for entry in ant_colony.objectives_over_time:
        for key, value in entry.items():
            objectives[key].append(value)

    questions = [
        inquirer.Checkbox(
            "graphs",
            message="What plots would you like to see?",
            choices=[
                "Objectives over time",
                "Flight path comparison",
                "Flight path over time",
                "3D Flight path over time",
            ],
            carousel=True,
        ),
    ]
    answers = inquirer.prompt(questions)

    # Display results
    display = Display()

    if "Objectives over time" in answers["graphs"]:
        show_objectives_over_time(display, objectives)

    if "Flight path comparison" in answers["graphs"]:
        show_flight_path_comparison(
            display,
            geodesic_path,
            real_flight_df,
            random_pareto_path_df,
            pareto_set,
            fp_cocip,
            aco_cocip,
        )

    if "Flight path over time" in answers["graphs"]:
        show_flight_frames(
            display,
            real_flight_df,
            random_pareto_path_df,
            contrail_grid.contrail_grid,
            config,
        )

    if "3D Flight path over time" in answers["graphs"]:
        show_3d_flight_frames(
            display,
            real_flight_df,
            random_pareto_path_df,
            contrail_polys,
            contrail_grid.contrail_grid,
            config,
        )

    display.show()


if __name__ == "__main__":
    app = typer.Typer()
    load_dotenv()
    warnings.filterwarnings("ignore")
    typer.run(main)
