import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import networkx as nx
import numpy as np

from .ant import Ant


class ACO:
    def __init__(self, routing_graph_manager, config):
        self.routing_graph_manager = routing_graph_manager
        self.routing_graph = routing_graph_manager.get_routing_graph()
        self.config = config

        self.objective_functions = [
            objective(self.routing_graph, self.config)
            for objective in config.OBJECTIVES
        ]
        self.objectives = [str(objective) for objective in self.objective_functions]
        self.objectives_over_time = []
        self.solutions = []
        self.pareto_set = []

    def check_pareto_dominance(self, solution):
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

    def run_aco_colony(self):
        best_objectives = dict.fromkeys(self.objectives, np.inf)

        ants = [
            Ant(
                self.routing_graph_manager,
                self.objective_functions,
                self.config,
            )
            for _ in range(self.config.NO_OF_ANTS)
        ]
        before2 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            for i in range(self.config.NO_OF_ITERATIONS):
                before = time.perf_counter()

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
                    is_dominated = self.check_pareto_dominance(solution)
                    if not is_dominated:
                        self.pareto_set.append(solution)

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
                after = time.perf_counter()
                print(f"iteration time: {after-before}")

        after2 = time.perf_counter()
        print(f"total time: {after2-before2}")

        return self.pareto_set

    def pheromone_update(self, solution, iteration_best_objective, best_objective):
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
