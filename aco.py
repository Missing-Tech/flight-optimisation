import math
import random
import time
from concurrent.futures import ProcessPoolExecutor

import networkx as nx
import numpy as np
import pandas as pd

import config
import util


objective_list = ["contrail", "co2", "time", "total"]
objective_functions = ["contrail", "co2", "time"]


class ACO:
    def __init__(self, rg, ag, cg, pm):
        self.routing_graph = rg.get_routing_graph()
        self.altitude_grid = ag.get_altitude_grid()
        self.contrail_grid = cg
        self.performance_model = pm

    def run_ant(self, id):
        solution = self.construct_solution()

        flight_path = util.convert_indices_to_points(
            solution, self.altitude_grid, self.routing_graph
        )
        flight_path = self.performance_model.calculate_flight_characteristics(
            flight_path
        )

        objectives = self.objective_function(flight_path)

        return solution, flight_path, objectives

    def run_aco_colony(self, iterations, no_of_ants):
        best_flight_path = None
        flight_paths = []
        objectives_list = []
        best_objective = dict.fromkeys(objective_list, np.inf)
        best_indexes = {}
        pareto_set = []

        before2 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=config.NO_OF_PROCESSES) as executor:
            for i in range(iterations):
                iteration_best_solution = dict.fromkeys(objective_list, None)
                iteration_best_objective = dict.fromkeys(objective_list, np.inf)

                # Run the ants
                ants = list(
                    executor.map(
                        self.run_ant,
                        range(no_of_ants),
                    )
                )

                # Get the results
                for ant in ants:
                    solution, flight_path, objectives = ant

                    flight_paths.append(flight_path)
                    is_dominated = False
                    for existing_solution in pareto_set:
                        if all(
                            objectives[objective] >= existing_solution[0][objective]
                            for objective in objective_functions
                        ):
                            is_dominated = True
                            break
                        elif all(
                            objectives[objective] <= existing_solution[0][objective]
                            for objective in objective_functions
                        ):
                            pareto_set.remove(existing_solution)
                    if not is_dominated:
                        pareto_set.append((objectives, flight_path))

                    for objective in objective_list:
                        if objectives[objective] < iteration_best_objective[objective]:
                            iteration_best_solution[objective] = solution
                            iteration_best_objective[objective] = objectives[objective]

                        if objectives[objective] < best_objective[objective]:
                            best_objective[objective] = objectives[objective]
                            if objective == "total":
                                best_flight_path = flight_path
                                best_indexes[i * ants.index(ant)] = flight_path

                objectives_list.append(iteration_best_objective)

                self.routing_graph = self.pheromone_update(
                    iteration_best_solution, iteration_best_objective, best_objective
                )

        after2 = time.perf_counter()
        print(f"total time: {after2-before2}")

        # get only the flight paths from the pareto set
        pareto_paths = [x[1] for x in pareto_set]
        pareto_df = [x[0] for x in pareto_set]

        objectives_df = pd.DataFrame.from_dict(objectives_list)
        pareto_df = pd.DataFrame.from_dict(pareto_df)
        return (
            flight_paths,
            best_flight_path,
            objectives_df,
            best_indexes,
            pareto_paths,
            pareto_df,
        )

    def calculate_objective_dataframe(self, flight_path):
        objectives = [self.objective_function(flight_path)]

        df = pd.DataFrame.from_dict(objectives)

        print(df)

        return df

    def calculate_contrail_ef(self, flight_path):
        contrail_ef = self.contrail_grid.interpolate_contrail_grid(flight_path)
        return contrail_ef

    def calculate_co2_ef(self, flight_path):
        fuel_burned = config.STARTING_WEIGHT - flight_path[-1]["aircraft_mass"]
        co2_per_kg = 4.70e9
        co2_penalty = fuel_burned * co2_per_kg
        return co2_penalty

    def calculate_flight_duration(self, flight_path):
        return (flight_path[-1]["time"] - flight_path[0]["time"]).seconds / 3600

    def objective_function(self, flight_path):
        co2_weight = config.CO2_WEIGHT
        contrail_weight = config.CONTRAIL_WEIGHT
        time_weight = config.TIME_WEIGHT

        co2_per_kg = 4.70e9
        co2_ef = self.calculate_co2_ef(flight_path)
        co2_penalty = math.pow(
            co2_ef / (config.STARTING_WEIGHT * co2_per_kg / 10), co2_weight
        )

        contrail_ef = self.calculate_contrail_ef(flight_path)
        contrail_penalty = math.pow(contrail_ef / 1e17, contrail_weight)

        flight_duration = self.calculate_flight_duration(flight_path)
        weighted_flight_duration = math.pow(flight_duration / 10, time_weight)

        total_penalty = co2_penalty + contrail_penalty + weighted_flight_duration

        return {
            "total": total_penalty,
            "contrail_ef": contrail_ef,
            "contrail": contrail_penalty,
            "co2_ef": co2_ef,
            "co2": co2_penalty,
            "flight_duration": flight_duration,
            "time": weighted_flight_duration,
            "arrival_time": flight_path[-1]["time"],
        }

    def pheromone_update(self, solution, iteration_best_objective, best_objective):
        evaporation_rate = config.EVAPORATION_RATE
        tau_min = config.TAU_MIN
        tau_max = config.TAU_MAX

        for objective in objective_functions:
            solution_edges = list(nx.utils.pairwise(solution[objective]))
            for u, v in solution_edges:
                delta = 0
                edge = self.routing_graph[u][v]
                delta = 1 / (
                    1 + iteration_best_objective[objective] - best_objective[objective]
                )

                new_pheromone = (1 - evaporation_rate) * (
                    edge[f"{objective}_pheromone"] + delta
                )

                self.routing_graph[u][v][f"{objective}_pheromone"] = max(
                    tau_min, min(new_pheromone, tau_max)
                )
        return self.routing_graph

    def construct_solution(self):
        solution = [(0, config.GRID_WIDTH, config.STARTING_ALTITUDE)]

        neighbours = self.routing_graph[solution[0]]
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

            solution.append(choice)
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
