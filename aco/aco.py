import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

import networkx as nx
import numpy as np

from .ant import Ant
from rich.progress import track

import typing

if typing.TYPE_CHECKING:
    from config import Config
    from routing_graph import RoutingGraphManager, RoutingGraph
    from types import Objectives
    from objectives import Objective
    from performance_model import Flight


class ACO:
    def __init__(self, routing_graph_manager: "RoutingGraphManager", config: "Config"):
        """
        Class to run the Ant Colony Optimisation algorithm
        """
        self.routing_graph_manager: "RoutingGraphManager" = routing_graph_manager
        self.routing_graph: "RoutingGraph" = routing_graph_manager.get_routing_graph()
        self.config: "Config" = config

        self.objective_functions: list["Objective"] = [
            objective(self.routing_graph_manager.performance_model, self.config)
            for objective in config.OBJECTIVES
        ]
        self.objectives: list[str] = [
            str(objective) for objective in self.objective_functions
        ]
        self.objectives_over_time: list["Objectives"] = []
        self.solutions: list["Flight"] = []
        self.pareto_set: list["Flight"] = []

    def check_pareto_dominance(self, solution: "Flight") -> bool:
        """
        Checks whether a solution belongs in the pareto set
        """
        for existing_solution in self.pareto_set:
            if all(
                solution.objectives[objective]
                >= existing_solution.objectives[objective]
                for objective in self.objectives
            ):
                return True
            elif all(
                solution.objectives[objective]
                <= existing_solution.objectives[objective]
                for objective in self.objectives
            ):
                self.pareto_set.remove(existing_solution)
        return False

    def run_aco_colony(self) -> list["Flight"]:
        """
        Runs the ACO algorithm and generates a pareto front of solutions
        """
        best_objectives = dict.fromkeys(self.objectives, np.inf)
        ants = [
            Ant(
                self.routing_graph_manager,
                self.objective_functions,
                self.config,
            )
            for _ in range(self.config.NO_OF_ANTS)
        ]
        for i in track(range(self.config.NO_OF_ITERATIONS)):
            with ProcessPoolExecutor(
                max_workers=multiprocessing.cpu_count()
            ) as executor:
                # Run the ants
                futures = [
                    executor.submit(ant.run_ant, i) for i, ant in enumerate(ants)
                ]

                iteration_best_solution = dict.fromkeys(self.objectives, None)
                iteration_best_objectives = dict.fromkeys(self.objectives, np.inf)

                # Get the results
                for future in as_completed(futures):
                    solution = future.result()

                    self.solutions.append(solution)
                    # Only add to the pareto set if it is not dominated by any current solution
                    is_dominated = self.check_pareto_dominance(solution)
                    if not is_dominated:
                        self.pareto_set.append(solution)

                    # Track the best objectives for each iteration and globally
                    for objective in self.objective_functions:
                        objective = str(objective)
                        if (
                            solution.objectives[objective]
                            < iteration_best_objectives[objective]
                        ):
                            iteration_best_solution[objective] = solution
                            iteration_best_objectives[objective] = solution.objectives[
                                objective
                            ]

                        if solution.objectives[objective] < best_objectives[objective]:
                            best_objectives[objective] = solution.objectives[objective]

                self.objectives_over_time.append(best_objectives.copy())
                self.pheromone_update(
                    iteration_best_solution, iteration_best_objectives, best_objectives
                )

        return self.pareto_set

    def pheromone_update(
        self,
        solution: "Flight",
        iteration_best_objective: "Objectives",
        best_objective: "Objectives",
    ) -> None:
        """
        Updates the pheromone structure based off the objective values
        """
        evaporation_rate = self.config.EVAPORATION_RATE
        tau_min = self.config.TAU_MIN
        tau_max = self.config.TAU_MAX

        for objective in self.objective_functions:
            objective = str(objective)
            solution_edges = list(nx.utils.pairwise(solution[objective].indices))
            for u, v in solution_edges:
                delta = 0
                edge = self.routing_graph[u][v]
                delta = 1 / max(
                    1, iteration_best_objective[objective] - best_objective[objective]
                )

                new_pheromone = (1 - evaporation_rate) * (
                    edge[f"{objective}_pheromone"] + delta
                )

                self.routing_graph[u][v][f"{objective}_pheromone"] = max(
                    tau_min, min(new_pheromone, tau_max)
                )
