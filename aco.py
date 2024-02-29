import numpy as np
import csv
import config
import time
import contrails as ct
import ecmwf
import flight_path as fp
import math
import random
import util
import networkx as nx
from concurrent.futures import ProcessPoolExecutor
import altitude_grid as ag
import functools
import routing_graph as rg


def run_ant(routing_graph, altitude_grid, contrail_grid, weather_data, ant_index):
    solution = construct_solution(routing_graph)

    thrusts = np.arange(config.INITIAL_THRUST, config.MAX_THRUST, config.MAX_THRUST_VAR)
    best_flight_path = None
    best_objective = None
    for thrust in thrusts:
        flight_path = util.convert_indices_to_points(
            solution, altitude_grid, thrust=thrust
        )
        flight_path = fp.calculate_flight_characteristics(flight_path, weather_data)
        objective = objective_function(flight_path, contrail_grid)
        if best_flight_path is None or objective < best_objective:
            best_flight_path = flight_path
            best_objective = objective

    return best_flight_path, best_objective


def run_aco_colony(
    iterations,
    no_of_ants,
):
    best_solution = None
    best_flight_path = None
    best_objective = None
    flight_paths = []
    contrail_grid = ct.get_contrail_grid()
    altitude_grid = ag.get_altitude_grid()
    routing_graph = rg.get_routing_graph()
    objectives = []

    weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
    before2 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=3) as executor:
        for _ in range(iterations):
            before = time.perf_counter()
            flight_paths = []

            run_ant_partial = functools.partial(
                run_ant,
                routing_graph,
                altitude_grid,
                contrail_grid,
                weather_data,
            )

            # Run the ants
            ants = list(executor.map(run_ant_partial, range(no_of_ants)))

            # Get the results
            for ant in ants:
                flight_path, objective = ant
                flight_paths.append(flight_path)
                if best_solution is None or objective < best_objective:
                    best_solution = flight_path
                    best_objective = objective
                    objectives.append(best_objective)
                    best_flight_path = flight_path

            routing_graph = pheromone_update(
                best_solution, routing_graph, best_objective
            )
            after = time.perf_counter()
            print(f"iteration time: {after-before}")
    with open("data/objectives.csv", "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(objectives)

    after2 = time.perf_counter()
    print(f"total time: {after2-before2}")

    return flight_paths, best_flight_path


def objective_function(flight_path, contrail_grid):
    co2_weight = config.CO2_WEIGHT
    contrail_weight = config.CONTRAIL_WEIGHT
    fuel_burned = config.STARTING_WEIGHT - flight_path[-1]["aircraft_mass"]
    co2_per_kg = 4.70e9

    contrail_ef = ct.interpolate_contrail_grid(contrail_grid, flight_path)
    contrail_penalty = (contrail_ef * contrail_weight) / 1e16
    co2_penalty = (fuel_burned * co2_per_kg * co2_weight) / (
        config.STARTING_WEIGHT * co2_per_kg / 10
    )

    ef_penalty = contrail_penalty + co2_penalty

    time_weight = config.TIME_WEIGHT
    flight_time_penalty = (
        time_weight * (flight_path[-1]["time"] - flight_path[0]["time"]).seconds / 3600
    ) / 2

    total_penalty = ef_penalty + flight_time_penalty

    return total_penalty


def pheromone_update(solution, routing_graph, best_objective):
    evaporation_rate = config.EVAPORATION_RATE
    tau_min = config.TAU_MIN
    tau_max = config.TAU_MAX

    solution_edges = list(nx.utils.pairwise(solution))

    for u, v in routing_graph.edges():
        delta = 0
        edge = routing_graph[u][v]
        if (u, v) in solution_edges:
            delta = 1 / (1 + best_objective)

        new_pheromone = (1 - evaporation_rate) * (edge["pheromone"] + delta)
        routing_graph[u][v]["pheromone"] = max(tau_min, min(new_pheromone, tau_max))
    return routing_graph


def construct_solution(routing_graph):
    solution = [(0, 0, config.STARTING_ALTITUDE)]

    neighbours = routing_graph[solution[0]]

    while neighbours:
        probabilities = []
        choice = None
        for n in neighbours:
            probability = calculate_probability_at_neighbour(
                n,
                routing_graph,
                neighbours[n]["pheromone"],
            )
            if probability == -1:
                # reached the destination
                choice = [n]
                break
            probabilities.append(probability)
        if not choice:
            choice = random.choices(list(neighbours), weights=probabilities, k=1)
        solution.append(choice[0])
        neighbours = routing_graph[choice[0]]

    return solution


def calculate_probability_at_neighbour(
    node,
    routing_graph,
    pheromone,
):
    heuristic = routing_graph.nodes[node]["heuristic"]
    total_neighbour_factor = 0
    neighbours = routing_graph[node]

    alpha = config.PHEROMONE_WEIGHT
    beta = config.HEURISTIC_WEIGHT

    if not neighbours:
        return -1
    for n in neighbours:
        total_neighbour_factor += math.pow(
            neighbours[n]["pheromone"], alpha
        ) * math.pow(routing_graph.nodes[n]["heuristic"], beta)

    probability = (
        math.pow(pheromone, alpha) * math.pow(heuristic, beta) / total_neighbour_factor
    )
    return probability
