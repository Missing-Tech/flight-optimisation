import numpy as np
import csv
import config
import time
import contrails as ct
import flight_path as fp
import math
import random
import util
import networkx as nx
from concurrent.futures import ProcessPoolExecutor
import pandas as pd


class ACO:
    def __init__(self, routing_graph, altitude_grid, contrail_grid):
        self.routing_graph = routing_graph
        self.altitude_grid = altitude_grid
        self.contrail_grid = contrail_grid

    def run_ant(self, id):
        solution = self.construct_solution()

        thrusts = np.arange(
            config.INITIAL_THRUST,
            config.MAX_THRUST + config.MAX_THRUST_VAR,
            config.MAX_THRUST_VAR,
        )
        best_flight_path = None
        best_objective = None
        best_solution = None
        for thrust in thrusts:
            flight_path = util.convert_indices_to_points(
                solution, self.altitude_grid, self.routing_graph, thrust=thrust
            )
            flight_path = fp.calculate_flight_characteristics(flight_path)
            objective = self.objective_function(flight_path)
            if best_flight_path is None or objective["total"] < best_objective["total"]:
                best_solution = solution
                best_flight_path = flight_path
                best_objective = objective

        return best_flight_path, best_objective, best_solution

    def run_aco_colony(self, iterations, no_of_ants):
        best_solution = None
        best_flight_path = None
        best_objective = None
        flight_paths = []
        objectives = []
        best_indexes = {}

        before2 = time.perf_counter()
        flight_paths = []
        with ProcessPoolExecutor(max_workers=config.NO_OF_PROCESSES) as executor:
            for i in range(iterations):
                iteration_best_solution = None
                iteration_best_objective = None

                # Run the ants
                before = time.perf_counter()
                ants = list(
                    executor.map(
                        self.run_ant,
                        range(no_of_ants),
                    )
                )
                after = time.perf_counter()
                print(f"iteration time: {after-before}")

                # Get the results
                for ant in ants:
                    flight_path, objective, solution = ant
                    flight_paths.append(flight_path)
                    objectives.append(objective)
                    if (
                        iteration_best_solution is None
                        or objective["total"] < iteration_best_objective["total"]
                    ):
                        iteration_best_solution = solution
                        iteration_best_objective = objective
                    if (
                        best_solution is None
                        or objective["total"] < best_objective["total"]
                    ):
                        best_solution = solution
                        best_objective = objective
                        best_indexes[i * ants.index(ant)] = best_flight_path
                        best_flight_path = flight_path

                self.routing_graph = self.pheromone_update(
                    iteration_best_solution, best_objective["total"]
                )

        after2 = time.perf_counter()
        print(f"total time: {after2-before2}")

        objectives_df = pd.DataFrame(objectives)

        return flight_paths, best_flight_path, objectives_df, best_indexes

    def calculate_objective_dataframe(self, flight_path):
        df = {}
        fuel_burned = config.STARTING_WEIGHT - flight_path[-1]["aircraft_mass"]
        co2_per_kg = 4.70e9

        contrail_ef = ct.interpolate_contrail_grid(self.contrail_grid, flight_path)
        co2_ef = fuel_burned * co2_per_kg

        flight_time_penalty = (
            flight_path[-1]["time"] - flight_path[0]["time"]
        ).seconds / 3600

        df["contrail_ef"] = contrail_ef
        df["co2_ef"] = co2_ef
        df["time"] = flight_time_penalty

        print(flight_path[-1]["time"])
        return df

    def objective_function(self, flight_path):
        co2_weight = config.CO2_WEIGHT
        contrail_weight = config.CONTRAIL_WEIGHT
        time_weight = config.TIME_WEIGHT
        fuel_burned = config.STARTING_WEIGHT - flight_path[-1]["aircraft_mass"]
        co2_per_kg = 4.70e9

        contrail_ef = ct.interpolate_contrail_grid(self.contrail_grid, flight_path)
        contrail_penalty = contrail_ef / 1e16
        co2_penalty = (fuel_burned * co2_per_kg) / (
            config.STARTING_WEIGHT * co2_per_kg / 10
        )

        ef_penalty = math.pow(contrail_penalty, -contrail_weight) + math.pow(
            co2_penalty, -co2_weight
        )

        flight_time_penalty = (
            (flight_path[-1]["time"] - flight_path[0]["time"]).seconds / 3600 / 10
        )

        total_penalty = ef_penalty + math.pow(flight_time_penalty, -time_weight)

        return {
            "total": total_penalty,
            "contrail_ef": contrail_ef,
            "fuel_burned": fuel_burned,
            "flight_duration": flight_time_penalty,
            "arrival_time": flight_path[-1]["time"],
        }

    def pheromone_update(self, solution, best_objective):
        evaporation_rate = config.EVAPORATION_RATE
        tau_min = config.TAU_MIN
        tau_max = config.TAU_MAX

        solution_edges = list(nx.utils.pairwise(solution))

        for u, v in solution_edges:
            delta = 0
            edge = self.routing_graph[u][v]
            delta = 1 / (1 + best_objective)

            new_pheromone = (1 - evaporation_rate) * (edge["pheromone"] + delta)

            self.routing_graph[u][v]["pheromone"] = max(
                tau_min, min(new_pheromone, tau_max)
            )
        return self.routing_graph

    def construct_solution(self):
        solution = [(0, config.GRID_WIDTH, config.STARTING_ALTITUDE)]

        neighbours = self.routing_graph[solution[0]]

        while neighbours:
            probabilities = []
            choice = None
            for n in neighbours:
                probability = self.calculate_probability_at_neighbour(
                    n,
                    neighbours[n]["pheromone"],
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
    ):
        heuristic = self.routing_graph.nodes[node]["heuristic"]
        total_neighbour_factor = 0
        neighbours = self.routing_graph[node]

        alpha = config.PHEROMONE_WEIGHT
        beta = config.HEURISTIC_WEIGHT

        if not neighbours:
            return -1
        for n in neighbours:
            total_neighbour_factor += math.pow(
                neighbours[n]["pheromone"], alpha
            ) * math.pow(self.routing_graph.nodes[n]["heuristic"], beta)

        probability = (
            math.pow(pheromone, alpha)
            * math.pow(heuristic, beta)
            / total_neighbour_factor
        )
        return probability
