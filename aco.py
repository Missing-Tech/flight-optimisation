import math
import multiprocessing
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import networkx as nx
import numpy as np
import pandas as pd

import config

from flight import Flight

objective_functions = ["contrail", "co2", "time"]


class Ant:
    def __init__(self, rg, ag, cg, pm):
        self.routing_graph = rg
        self.altitude_grid = ag
        self.contrail_grid = cg
        self.performance_model = pm

    def run_ant(self, id):
        solution = self.construct_solution()
        solution.run_performance_model()
        objectives = self.objective_function(solution.flight_path)
        solution.set_objective_value(objectives)

        return solution

    def calculate_contrail_ef(self, flight_path):
        contrail_ef = self.contrail_grid.interpolate_contrail_grid(flight_path)
        return contrail_ef

    def calculate_co2_kg(self, flight_path, flight_duration):
        co2_kg = (
            sum(point["CO2"] for point in flight_path)
            * flight_duration
            * 3600
            / 1000  # convert g/s to kg
        )
        return co2_kg  # convert to ef

    def calculate_flight_duration(self, flight_path):
        return (flight_path[-1]["time"] - flight_path[0]["time"]).seconds / 3600

    def objective_function(self, flight_path):
        co2_weight = config.CO2_WEIGHT
        contrail_weight = config.CONTRAIL_WEIGHT
        time_weight = config.TIME_WEIGHT

        contrail_ef = self.calculate_contrail_ef(flight_path)
        contrail_penalty = contrail_ef * contrail_weight

        flight_duration = self.calculate_flight_duration(flight_path)
        weighted_flight_duration = flight_duration * time_weight

        co2_kg = self.calculate_co2_kg(flight_path, flight_duration)
        co2_penalty = co2_kg * co2_weight

        return {
            "contrail": contrail_penalty,
            "co2": co2_penalty,
            "time": weighted_flight_duration,
        }

    def construct_solution(self):
        solution = Flight(
            self.altitude_grid,
            self.routing_graph,
            self.performance_model,
            flight_path=[],
        )
        solution.set_departure(((0, config.GRID_WIDTH, config.STARTING_ALTITUDE)))

        neighbours = self.routing_graph[solution.indices[0]]
        while neighbours:
            probabilities = []
            choice = None
            random_objective = random.choice(objective_functions)
            for n in neighbours:
                probability = self.calculate_probability_at_neighbour(
                    n,
                    neighbours[n][f"{random_objective}_pheromone"],
                    random_objective,
                )
                if probability == -1:
                    # reached the destination
                    choice = n
                    break
                probabilities.append(probability)
            if not choice:
                choice = random.choices(list(neighbours), weights=probabilities, k=1)[0]

            solution.add_point_from_index(choice)
            neighbours = self.routing_graph[choice]

        return solution

    def calculate_probability_at_neighbour(
        self,
        node,
        pheromone,
        objective,
    ):
        heuristic = self.routing_graph.nodes[node][f"{objective}_heuristic"]
        total_neighbour_factor = 0.01
        neighbours = self.routing_graph[node]

        alpha = config.PHEROMONE_WEIGHT
        beta = config.HEURISTIC_WEIGHT

        if not neighbours:
            return -1
        for n in neighbours:
            total_neighbour_factor += math.pow(
                neighbours[n][f"{objective}_pheromone"], alpha
            ) * math.pow(self.routing_graph.nodes[n][f"{objective}_heuristic"], beta)

        probability = (
            math.pow(pheromone, alpha) * math.pow(heuristic, beta)
        ) / total_neighbour_factor
        return probability


class ACO:
    def __init__(self, rg, ag, cg, pm):
        self.routing_graph = rg.get_routing_graph()
        self.altitude_grid = ag.get_altitude_grid()
        self.contrail_grid = cg
        self.performance_model = pm

    def run_aco_colony(self, iterations, no_of_ants):
        solutions = []
        objectives_list = []
        best_objective = dict.fromkeys(objective_functions, np.inf)
        best_indexes = {}
        pareto_set = []

        ants = [
            Ant(
                self.routing_graph,
                self.altitude_grid,
                self.contrail_grid,
                self.performance_model,
            )
            for _ in range(config.NO_OF_ANTS)
        ]
        before2 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            for i in range(iterations):
                before = time.perf_counter()

                # Run the ants
                futures = [
                    executor.submit(ant.run_ant, i) for i, ant in enumerate(ants)
                ]

                iteration_best_solution = dict.fromkeys(objective_functions, None)
                iteration_best_objective = dict.fromkeys(objective_functions, np.inf)

                # Get the results
                for future in as_completed(futures):
                    solution = future.result()

                    solutions.append(solution)
                    is_dominated = False
                    for existing_solution in pareto_set:
                        if all(
                            solution.objectives[objective]
                            >= existing_solution.objectives[objective]
                            for objective in objective_functions
                        ):
                            is_dominated = True
                            break
                        elif all(
                            solution.objectives[objective]
                            <= existing_solution.objectives[objective]
                            for objective in objective_functions
                        ):
                            pareto_set.remove(existing_solution)
                    if not is_dominated:
                        pareto_set.append(solution)

                    for objective in objective_functions:
                        if (
                            solution.objectives[objective]
                            < iteration_best_objective[objective]
                        ):
                            iteration_best_solution[objective] = solution
                            iteration_best_objective[objective] = solution.objectives[
                                objective
                            ]

                        if solution.objectives[objective] < best_objective[objective]:
                            best_objective[objective] = solution.objectives[objective]

                objectives_list.append(iteration_best_objective)

                self.routing_graph = self.pheromone_update(
                    iteration_best_solution, iteration_best_objective, best_objective
                )
                after = time.perf_counter()
                print(f"iteration time: {after-before}")

        after2 = time.perf_counter()
        print(f"total time: {after2-before2}")

        # get only the flight paths from the pareto set
        pareto_paths = [x.flight_path for x in pareto_set]
        pareto_df = [x.objectives for x in pareto_set]

        objectives_df = pd.DataFrame.from_dict([x for x in objectives_list])
        pareto_df = pd.DataFrame.from_dict(pareto_df)
        best_solution = random.choice(pareto_set)
        print(best_solution.objectives)
        return (
            solutions,
            best_solution,
            objectives_df,
            best_indexes,
            pareto_paths,
            pareto_df,
        )

    def pheromone_update(self, solution, iteration_best_objective, best_objective):
        evaporation_rate = config.EVAPORATION_RATE
        tau_min = config.TAU_MIN
        tau_max = config.TAU_MAX

        for objective in objective_functions:
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
        return self.routing_graph
