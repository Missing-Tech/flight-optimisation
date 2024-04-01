from __future__ import print_function, unicode_literals
import random
import warnings
from dotenv import load_dotenv
import pandas as pd
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import inquirer
import pickle
from pathlib import Path
import os
import graphs
from config import (
    Config,
    ContrailMaxConfig,
    ContrailConfig,
    CO2Config,
    TimeConfig,
    CocipConfig,
)
from objectives import ContrailObjective, CO2Objective, TimeObjective, CocipObjective
from routing_graph import RoutingGraphManager
from performance_model import PerformanceModel, RealFlight, RandomFlight
from aco import ACO
from display import Display


def load_pickle(file_path):
    with open(file_path, "rb") as f:
        return pickle.load(f)


def save_pickle(file_path, data):
    Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        pickle.dump(data, f)


def load_csv(file_path):
    return pd.read_csv(file_path)


def save_csv(file_path, data):
    Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
    data.to_csv(file_path, index=False)


def print_results_table(real_flight, random_flight, pareto_set, chosen_pareto_path):
    real_flight_objectives = real_flight.objectives
    random_flight_objectives = random_flight.objectives

    table = Table()
    table.add_column("Solution", style="bold")
    table.add_column("Contrail EF", style="blue italic")
    table.add_column("kg of CO2", style="red italic")
    table.add_column("Time (h)", style="green italic")
    table.add_row(
        "[blue]Real Flight[/blue]",
        "{:.3g}".format(real_flight_objectives["contrail"]),
        "{:.3g}".format(real_flight_objectives["co2"]),
        "{:.3g}".format(real_flight_objectives["time"]),
    )
    table.add_row(
        "[green]Rand. Flight[/green]",
        "{:.3g}".format(random_flight_objectives["contrail"]),
        "{:.3g}".format(random_flight_objectives["co2"]),
        "{:.3g}".format(random_flight_objectives["time"]),
    )
    for i, solution in enumerate(pareto_set):
        name = f"Solution {i + 1}"
        if chosen_pareto_path is not None:
            if solution.flight_path == chosen_pareto_path.flight_path:
                name = "[red]Chosen Path[/red]"
        table.add_row(
            name,
            "{:.3g}".format(solution.objectives["contrail"]),
            "{:.3g}".format(solution.objectives["co2"]),
            "{:.3g}".format(solution.objectives["time"]),
        )

    print(table)
    print("\n \n \n")  # Add some space between the table and the next question


def run_aco(config: Config, choose_path=False):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating altitude grid...", total=None)
        routing_graph_manager = RoutingGraphManager(config)
        geodesic_path = routing_graph_manager.get_geodesic_path()
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
    objectives = ant_colony.objectives
    print("[bold green]:white_check_mark: ACO complete.[/bold green]")

    # Run performance model on a real flight
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Running performance model on real flight...", total=None
        )
        real_flight = RealFlight("jan-31-cleaned.csv", routing_graph_manager, config)
        real_flight.run_performance_model()
    print(
        "[bold green]:white_check_mark: Performance model run on real flight.[/bold green]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating a random flight path...", total=None)
        random_flight_path = RandomFlight(routing_graph_manager, config)
        random_flight_path.construct_random_flight()
        random_flight_path.run_performance_model()
    print("[bold green]:white_check_mark: Created a random flight path.[/bold green]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Recalculating objectives...", total=None)
        # Recalculate objectives
        objective_list = [
            ContrailObjective,
            CO2Objective,
            TimeObjective,
            CocipObjective,
        ]
        config.OBJECTIVES = objective_list

        random_flight_path.config = config
        real_flight.config = config
        random_flight_path.calculate_objectives()
        real_flight.calculate_objectives()
        for path in pareto_set:
            path.config = config
            path.calculate_objectives()

    print_results_table(real_flight, random_flight_path, pareto_set, None)

    if choose_path:
        questions = [
            inquirer.List(
                "results",
                message="What path would you like to choose?",
                choices=[i + 1 for i, _ in enumerate(pareto_set)],
                carousel=True,
            )
        ]
        answers = inquirer.prompt(questions)
        chosen_pareto_path = pareto_set[answers["results"] - 1]
    else:
        chosen_pareto_path = random.choice(pareto_set)

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
            chosen_pareto_path.flight_path
        )
        rand_ef, rand_df, rand_cocip = cocip_manager.calculate_ef_from_flight_path(
            random_flight_path.flight_path
        )
    print(
        "[bold green]:white_check_mark: CoCiP calculated for both flights.[/bold green]"
    )

    return (
        geodesic_path,
        real_flight,
        random_flight_path,
        chosen_pareto_path,
        pareto_set,
        objectives,
        fp_cocip,
        aco_cocip,
        rand_cocip,
        contrail_grid,
        contrail_polys,
    )


def save_results(dir: str, results, config):
    (
        geodesic_path,
        real_flight,
        random_flight_path,
        chosen_pareto_path,
        pareto_set,
        objectives,
        fp_cocip,
        aco_cocip,
        rand_cocip,
        contrail_grid,
        contrail_polys,
    ) = results
    save_pickle(f"{dir}geodesic_path.pkl", geodesic_path)
    save_pickle(f"{dir}real_flight.pkl", real_flight)
    save_pickle(f"{dir}chosen_pareto_path.pkl", chosen_pareto_path)
    save_pickle(f"{dir}random_flight.pkl", random_flight_path)
    save_pickle(f"{dir}pareto_set.pkl", pareto_set)
    save_pickle(f"{dir}fp_cocip.pkl", fp_cocip)
    save_pickle(f"{dir}aco_cocip.pkl", aco_cocip)
    save_pickle(f"{dir}rand_cocip.pkl", rand_cocip)
    save_pickle(f"{dir}contrail_grid.pkl", contrail_grid)
    save_pickle(f"{dir}contrail_polys.pkl", contrail_polys)
    save_pickle(f"{dir}config.pkl", config)
    save_csv(f"{dir}objectives.csv", pd.DataFrame(objectives))
    save_csv(
        f"{dir}real_flight_objectives.csv",
        pd.DataFrame(real_flight.objectives, index=[0]),
    )
    pareto_set_objectives = [solution.objectives for solution in pareto_set]
    save_csv(
        f"{dir}pareto_set_objectives.csv",
        pd.DataFrame(pareto_set_objectives),
    )
    save_csv(
        f"{dir}random_objectives.csv",
        pd.DataFrame(random_flight_path.objectives, index=[0]),
    )


def load_results(dir: str):
    geodesic_path = load_pickle(f"{dir}geodesic_path.pkl")
    real_flight = load_pickle(f"{dir}real_flight.pkl")
    chosen_pareto_path = load_pickle(f"{dir}chosen_pareto_path.pkl")
    random_flight_path = load_pickle(f"{dir}random_flight.pkl")
    pareto_set = load_pickle(f"{dir}pareto_set.pkl")
    objectives = load_csv(f"{dir}objectives.csv")
    fp_cocip = load_pickle(f"{dir}fp_cocip.pkl")
    aco_cocip = load_pickle(f"{dir}aco_cocip.pkl")
    rand_cocip = load_pickle(f"{dir}rand_cocip.pkl")
    contrail_grid = load_pickle(f"{dir}contrail_grid.pkl")
    contrail_polys = load_pickle(f"{dir}contrail_polys.pkl")
    config = load_pickle(f"{dir}config.pkl")

    return (
        geodesic_path,
        real_flight,
        random_flight_path,
        chosen_pareto_path,
        pareto_set,
        objectives,
        fp_cocip,
        aco_cocip,
        rand_cocip,
        contrail_grid,
        contrail_polys,
        config,
    )


def save_figs(dir: str, results, config):
    display = Display()
    (
        geodesic_path,
        real_flight,
        random_flight_path,
        chosen_pareto_path,
        pareto_set,
        objectives,
        fp_cocip,
        aco_cocip,
        rand_cocip,
        contrail_grid,
        contrail_polys,
    ) = results
    geodesic_path = pd.DataFrame(geodesic_path, columns=["latitude", "longitude"])
    real_flight_df = pd.DataFrame(
        real_flight.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )
    chosen_pareto_path_df = pd.DataFrame(
        chosen_pareto_path.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )
    random_path_df = pd.DataFrame(
        random_flight_path.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )
    fig1 = graphs.show_flight_path_comparison(
        display,
        geodesic_path,
        real_flight_df,
        chosen_pareto_path_df,
        random_path_df,
        pareto_set,
        fp_cocip,
        aco_cocip,
        rand_cocip,
    )

    fig2 = graphs.show_flight_frames(
        display,
        real_flight_df,
        chosen_pareto_path_df,
        random_path_df,
        contrail_grid.contrail_grid,
        config,
    )

    fig3 = graphs.show_3d_flight_frames(
        display,
        real_flight_df,
        chosen_pareto_path_df,
        random_path_df,
        contrail_polys,
        contrail_grid.contrail_grid,
        config,
    )
    Path(dir).mkdir(parents=True, exist_ok=True)

    fig1.savefig(f"{dir}flight_path_comparison.png", dpi=300)
    fig2.savefig(f"{dir}flight_frames.png", dpi=300)
    fig3.savefig(f"{dir}3d_flight_frames.png", dpi=300)


def result_run(config, dir: str):
    # Construct all required grids + models
    results = run_aco(config)

    save_results(f"{dir}pickles/", results, config)
    save_figs(f"{dir}figs/", results, config)


def automate_results():
    configs = [
        Config(),
        ContrailConfig(),
        CO2Config(),
        TimeConfig(),
    ]
    iterations = [1, 10, 50, 100, 200]
    evaporation_rates = [0.2, 0.5, 0.8]
    no_of_ants = [1, 8, 16]
    constants = {
        "no_of_iterations": 100,
        "evaporation_rate": 0.5,
        "no_of_ants": 8,
    }
    questions = [
        inquirer.Checkbox(
            "results",
            message="What results would you like to collect?",
            choices=[
                "Iterations",
                "Configs",
                "Evaporation rates",
                "No of ants",
            ],
            carousel=True,
        )
    ]
    answers = inquirer.prompt(questions)

    if "Iterations" in answers["results"]:
        print("[bold blue]Collecting iterations data...[/bold blue]")
        for iteration in iterations:
            print(f"[blue]Running {iteration} iterations...[/blue]")
            config = Config()
            config.NO_OF_ITERATIONS = iteration
            config.EVAPORATION_RATE = constants["evaporation_rate"]
            config.NO_OF_ANTS = constants["no_of_ants"]
            result_run(config, f"results/iterations/{iteration}/")

    if "Configs" in answers["results"]:
        print("[bold blue]Collecting configs data...[/bold blue]")
        for config in configs:
            print(f"[blue]Running {config.NAME}...[/blue]")
            config.NO_OF_ITERATIONS = constants["no_of_iterations"]
            config.EVAPORATION_RATE = constants["evaporation_rate"]
            config.NO_OF_ANTS = constants["no_of_ants"]
            result_run(config, f"results/configs/{config.NAME}/")

    if "Evaporation rates" in answers["results"]:
        print("[bold blue]Collecting evaporation rates data...[/bold blue]")
        for evaporation_rate in evaporation_rates:
            print(f"[blue]Running {evaporation_rate} evaporation rate...[/blue]")
            config = Config()
            config.EVAPORATION_RATE = evaporation_rate
            config.NO_OF_ITERATIONS = constants["no_of_iterations"]
            config.NO_OF_ANTS = constants["no_of_ants"]
            result_run(config, f"results/evaporation_rates/{evaporation_rate}/")

    if "No of ants" in answers["results"]:
        print("[bold blue]Collecting no of ants data...[/bold blue]")
        for no_of_ant in no_of_ants:
            print(f"[blue]Running {no_of_ant} ants...[/blue]")
            config = Config()
            config.NO_OF_ANTS = no_of_ant
            config.NO_OF_ITERATIONS = constants["no_of_iterations"]
            config.EVAPORATION_RATE = constants["evaporation_rate"]
            result_run(config, f"results/no_of_ants/{no_of_ant}/")

    print("[bold green]:white_check_mark: Results collected.[/bold green]")


def main():
    questions = [
        inquirer.List(
            "choice",
            message="What would you like to do?",
            choices=["Run ACO", "Load ACO Results", "Automate Results"],
            carousel=True,
        ),
    ]

    answers = inquirer.prompt(questions)

    if answers["choice"] == "Automate Results":
        automate_results()
        print("[bold green]:white_check_mark: Results automated.[/bold green]")
        return

    if answers["choice"] == "Load ACO Results":
        questions = [
            inquirer.Path(
                "dir",
                message="Where are the results located?",
                default="results/user/",
                path_type=inquirer.Path.DIRECTORY,
            ),
        ]
        answers = inquirer.prompt(questions)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Loading results...", total=None)
            results = load_results(answers["dir"])
            (
                geodesic_path,
                real_flight,
                random_flight_path,
                chosen_pareto_path,
                pareto_set,
                objectives,
                fp_cocip,
                aco_cocip,
                rand_cocip,
                contrail_grid,
                contrail_polys,
                config,
            ) = results

            print_results_table(
                real_flight,
                random_flight_path,
                pareto_set,
                chosen_pareto_path,
            )
        print("[bold green]:white_check_mark: Results loaded.[/bold green]")

    else:
        questions = [
            inquirer.List(
                "config",
                message="Which configuration would you like to use?",
                choices=["Default", "ContrailMax", "Contrail", "CO2", "Time", "CoCiP"],
                carousel=True,
            ),
            inquirer.List(
                "iterations",
                message="How many iterations would you like to run?",
                choices=[1, 10, 50, 100, 200],
                carousel=True,
            ),
            inquirer.List(
                "evaporation_rate",
                message="Choose an evaporation rate.",
                choices=[0.2, 0.5, 0.8],
                carousel=True,
            ),
            inquirer.List(
                "no_of_ants",
                message="Choose a number of ants.",
                choices=[1, 8, 16],
                carousel=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers["config"] == "Default":
            config = Config()
        elif answers["config"] == "Contrail":
            config = ContrailConfig()
        elif answers["config"] == "CO2":
            config = CO2Config()
        elif answers["config"] == "Time":
            config = TimeConfig()
        elif answers["config"] == "CoCiP":
            config = CocipConfig()
        else:
            config = ContrailMaxConfig()

        config.NO_OF_ITERATIONS = answers["iterations"]
        config.EVAPORATION_RATE = answers["evaporation_rate"]
        config.NO_OF_ANTS = answers["no_of_ants"]

        # Construct all required grids + models
        results = run_aco(config, choose_path=True)
        (
            geodesic_path,
            real_flight,
            random_flight_path,
            chosen_pareto_path,
            pareto_set,
            objectives,
            fp_cocip,
            aco_cocip,
            rand_cocip,
            contrail_grid,
            contrail_polys,
        ) = results

        questions = [
            inquirer.Confirm(
                "save",
                message="Would you like to save the results?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers["save"]:
            questions = [
                inquirer.Path(
                    "dir",
                    message="Where would you like to save the results?",
                    default="results/user/",
                    path_type=inquirer.Path.DIRECTORY,
                ),
            ]
            answers = inquirer.prompt(questions)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(
                    description="Saving results...",
                    total=None,
                )
                save_results(answers["dir"], results, config)

            print("[bold green]:white_check_mark: Results saved.[/bold green]")

    geodesic_path = pd.DataFrame(geodesic_path, columns=["latitude", "longitude"])
    real_flight_df = pd.DataFrame(
        real_flight.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )
    chosen_pareto_path_df = pd.DataFrame(
        chosen_pareto_path.flight_path,
        columns=["latitude", "longitude", "time", "altitude_ft"],
    )
    random_path_df = pd.DataFrame(
        random_flight_path.flight_path,
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
            chosen_pareto_path_df,
            random_path_df,
            pareto_set,
            fp_cocip,
            aco_cocip,
            rand_cocip,
        )

    if "Flight path over time" in answers["graphs"]:
        graphs.show_flight_frames(
            display,
            real_flight_df,
            chosen_pareto_path_df,
            random_path_df,
            contrail_grid.contrail_grid,
            config,
        )

    if "3D Flight path over time" in answers["graphs"]:
        graphs.show_3d_flight_frames(
            display,
            real_flight_df,
            chosen_pareto_path_df,
            random_path_df,
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
