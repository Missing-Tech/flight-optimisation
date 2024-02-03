import numpy as np
import time
import contrails as ct
import ecmwf
import flight_path as fp
import math
import random
import util
import networkx as nx


def run_aco_colony(iterations, no_of_ants, routing_graph, altitude_grid, distance):
    best_solution = None
    best_flight_path = None
    best_objective = None
    flight_paths = []
    contrail_grid = ct.download_contrail_grid(altitude_grid)
    for _ in range(iterations):
        before = time.perf_counter()
        flight_paths = []
        ants = []
        for ant in range(no_of_ants):
            solution = construct_solution(routing_graph)
            ants.append(solution)

            flight_path = util.convert_indices_to_points(solution, altitude_grid)
            weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
            flight_path = fp.calculate_flight_characteristics(flight_path, weather_data)
            flight_paths.append(flight_path)
            objective = objective_function(flight_path, distance, contrail_grid)

            if best_solution is None or objective < best_objective:
                best_solution = solution
                best_objective = objective
                best_flight_path = flight_path

            routing_graph = pheromone_update(
                best_solution, routing_graph, best_objective
            )
        after = time.perf_counter()
        print(f"time: {after-before}")

    return flight_paths, best_flight_path


def objective_function(flight_path, distance, contrail_grid):
    co2_weight = 1
    contrail_weight = 3
    fuel_burned = 60000 - flight_path[-1]["aircraft_mass"]
    co2_per_kg = 4.70e9

    contrail_ef = ct.interpolate_contrail_grid(contrail_grid, flight_path, distance)

    return (
        (fuel_burned * co2_per_kg * co2_weight) + (contrail_ef * contrail_weight)
    ) / 1e14


def pheromone_update(solution, routing_graph, best_objective):
    evaporation_rate = 0.5
    tau_min = 1
    tau_max = 10

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
    solution = [(0, 0, 30000)]

    neighbours = routing_graph[solution[0]]

    while neighbours:
        probabilities = []
        choice = None
        for n in neighbours:
            probability = calculate_probability_at_neighbour(
                n, routing_graph, 1, 4, neighbours[n]["pheromone"], solution
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
    node, routing_graph, alpha, beta, pheromone, solution
):
    heuristic = routing_graph.nodes[node]["heuristic"]
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
