from __future__ import print_function, unicode_literals
import random
import warnings
from dotenv import load_dotenv
import pandas as pd
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
import inquirer
import pickle

import graphs
from config import Config, ContrailMaxConfig
from routing_graph import RoutingGraphManager
from performance_model import PerformanceModel, RealFlight
from aco import ACO
from display import Display


def load_pickle(file_path):
    with open(file_path, "rb") as f:
        return pickle.load(f)


def save_pickle(file_path, data):
    with open(file_path, "wb") as f:
        pickle.dump(data, f)


def main():
    questions = [
        inquirer.List(
            "choice",
            message="What would you like to do?",
            choices=["Run ACO", "Load ACO Results"],
            carousel=True,
        ),
    ]

    answers = inquirer.prompt(questions)
    if answers["choice"] == "Load ACO Results":
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Loading results...", total=None)
            geodesic_path = load_pickle("results/geodesic_path.pkl")
            real_flight = load_pickle("results/real_flight.pkl")
            random_pareto_path = load_pickle("results/random_pareto_path.pkl")
            pareto_set = load_pickle("results/pareto_set.pkl")
            objectives = load_pickle("results/objectives.pkl")
            fp_cocip = load_pickle("results/fp_cocip.pkl")
            aco_cocip = load_pickle("results/aco_cocip.pkl")
            contrail_grid = load_pickle("results/contrail_grid.pkl")
            contrail_polys = load_pickle("results/contrail_polys.pkl")
            config = load_pickle("results/config.pkl")
        print("[bold green]:white_check_mark: Results loaded.[/bold green]")
    else:
        questions = [
            inquirer.List(
                "config",
                message="Which configuration would you like to use?",
                choices=["Default", "ContrailMax"],
                carousel=True,
            ),
            inquirer.List(
                "iterations",
                message="How many iterations would you like to run?",
                choices=[1, 10, 100, 300, 1000],
                carousel=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers["config"] == "Default":
            config = Config()
        else:
            config = ContrailMaxConfig()

        config.NO_OF_ITERATIONS = answers["iterations"]

        # Construct all required grids + models
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Creating altitude grid...", total=None)
            routing_graph_manager = RoutingGraphManager(config)
            geodesic_path = routing_graph_manager.get_geodesic_path()
            # routing_grid = routing_graph_manager.get_routing_grid()
            # altitude_grid = routing_graph_manager.get_altitude_grid()
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
        print(
            "[bold green]:white_check_mark: Performance model constructed.[/bold green]"
        )

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
            progress.add_task(
                description="Running CoCiP for both flights...", total=None
            )
            fp_ef, fp_df, fp_cocip = cocip_manager.calculate_ef_from_flight_path(
                real_flight.flight_path
            )
            aco_ef, aco_df, aco_cocip = cocip_manager.calculate_ef_from_flight_path(
                random_pareto_path.flight_path
            )
        print(
            "[bold green]:white_check_mark: CoCiP calculated for both flights.[/bold green]"
        )

        objectives = {key: [] for key in ant_colony.objectives_over_time[0].keys()}
        for entry in ant_colony.objectives_over_time:
            for key, value in entry.items():
                objectives[key].append(value)
        questions = [
            inquirer.Confirm(
                "save",
                message="Would you like to save the results?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers["save"]:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(
                    description="Saving results...",
                    total=None,
                )
                save_pickle("results/geodesic_path.pkl", geodesic_path)
                save_pickle("results/real_flight.pkl", real_flight)
                save_pickle("results/random_pareto_path.pkl", random_pareto_path)
                save_pickle("results/pareto_set.pkl", pareto_set)
                save_pickle("results/objectives.pkl", objectives)
                save_pickle("results/fp_cocip.pkl", fp_cocip)
                save_pickle("results/aco_cocip.pkl", aco_cocip)
                save_pickle("results/contrail_grid.pkl", contrail_grid)
                save_pickle("results/contrail_polys.pkl", contrail_polys)
                save_pickle("results/config.pkl", config)
            print("[bold green]:white_check_mark: Results saved.[/bold green]")

    # Create required dataframes
    # grid = sum(routing_grid.get_routing_grid(), [])
    # routing_grid_df = pd.DataFrame(grid, columns=["latitude", "longitude"])

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
        graphs.show_objectives_over_time(display, objectives)

    if "Flight path comparison" in answers["graphs"]:
        graphs.show_flight_path_comparison(
            display,
            geodesic_path,
            real_flight_df,
            random_pareto_path_df,
            pareto_set,
            fp_cocip,
            aco_cocip,
        )

    if "Flight path over time" in answers["graphs"]:
        graphs.show_flight_frames(
            display,
            real_flight_df,
            random_pareto_path_df,
            contrail_grid.contrail_grid,
            config,
        )

    if "3D Flight path over time" in answers["graphs"]:
        graphs.show_3d_flight_frames(
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
