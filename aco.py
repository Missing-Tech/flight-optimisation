import numpy as np
import time
import contrails as ct
import ecmwf
import flight_path as fp
import math
import random
import util
import networkx as nx


def run_aco_colony(iterations, no_of_ants, routing_graph, altitude_grid):
    ants = []
    flight_paths = []
    best_solution = None
    best_flight_path = None
    ef_values = {}
    for _ in range(iterations):
        before = time.perf_counter()
        flight_paths = []
        ants = []
        for ant in range(no_of_ants):
            solution, flight_path = construct_solution(routing_graph, altitude_grid)
            ants.append(solution)
            flight_paths.append(flight_path)

            if best_solution is None or objective_function(
                flight_path, altitude_grid
            ) < objective_function(best_flight_path, altitude_grid):
                best_solution = solution
                best_flight_path = flight_path

        for ant in ants:
            routing_graph = pheromone_update(
                ant,
                best_solution,
                routing_graph,
                altitude_grid,
                flight_path,
                best_flight_path,
            )
            if objective_function(flight_path, altitude_grid) < objective_function(
                best_flight_path, altitude_grid
            ):
                best_solution = ant
                best_flight_path = flight_paths[ants.index(ant)]

        after = time.perf_counter()
        print(f"time taken: {after-before}")
    return best_flight_path


def objective_function(solution, altitude_grid):
    contrail_grid = ct.download_contrail_grid(altitude_grid)
    ef = ct.interpolate_contrail_grid(contrail_grid, solution)
    return ef


def pheromone_update(
    solution, best_solution, routing_graph, altitude_grid, flight_path, best_flight_path
):
    evaporation_rate = 0.5
    tau_min = 1
    tau_max = 10

    for u, v in zip(solution[:-1], solution[1:]):
        edge = routing_graph[u][v]
        delta = (
            1 / 1
            + objective_function(flight_path, altitude_grid)
            - objective_function(best_flight_path, altitude_grid)
        )
        new_pheromone = (1 - evaporation_rate) * edge["pheromone"] + delta
        routing_graph[u][v]["pheromone"] = max(tau_min, min(new_pheromone, tau_max))
    return routing_graph


def construct_solution(routing_graph, altitude_grid):
    solution = [(0, 0, 30000)]

    neighbours = routing_graph[solution[0]]

    while neighbours:
        probabilities = []
        choice = None
        for n in neighbours:
            probability = calculate_probability_at_neighbour(
                n, routing_graph, 1, 2, neighbours[n]["pheromone"], solution
            )
            if probability == -1:
                choice = [n]
                break
            probabilities.append(probability)
        if not choice:
            choice = random.choices(list(neighbours), weights=probabilities, k=1)
        solution.append(choice[0])
        neighbours = routing_graph[choice[0]]

    flight_path = util.convert_indices_to_points(solution, altitude_grid)
    weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
    flight_path = fp.calculate_flight_characteristics(flight_path, weather_data)
    return solution, flight_path


def calculate_heuristic(node, routing_graph, solution):
    current_heuristic = routing_graph.nodes[node]["heuristic"]
    return random.random()


def calculate_probability_at_neighbour(
    node, routing_graph, alpha, beta, pheromone, solution
):
    heuristic = calculate_heuristic(node, routing_graph, solution)
    total_neighbour_factor = 0
    neighbours = routing_graph[node]
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
